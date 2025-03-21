import os
import json
import discord
import random
import asyncio

from Modules.db_control import read_from_guild_settings_db, write_to_buttons_db, read_member_data_from_db
from Modules.text_channels_control import add_game_in_game_roles_channel
from utils import clean_channel_id, get_bot, is_game_valid, get_logger
from Modules.phrases import get_phrase
from Modules.buttons import JoinButton, VoiceChannelCcontrol

temp_channels_path = os.path.join("Data", "temp_channels.json")

bot = get_bot()
logger = get_logger()

def load_temp_channels():
    if os.path.exists(temp_channels_path):
        with open(temp_channels_path, "r") as f:
            return json.load(f)
    return {}

def save_temp_channels(temp_channels):
    os.makedirs(os.path.dirname(temp_channels_path), exist_ok=True)
    with open(temp_channels_path, "w") as f:
        json.dump(temp_channels, f, indent=4)


async def check_and_remove_nonexistent_channels():
    temp_channels = load_temp_channels()

    for channel_id, channel_info in list(temp_channels.items()):
        guild_id = channel_info['guild_id']
        guild = bot.get_guild(guild_id)

        if guild is not None:
            channel = guild.get_channel(int(channel_id))

            if channel is None:
                del temp_channels[channel_id]

    save_temp_channels(temp_channels)

async def find_party_controller(member, before, after):
    logger.info(f"[START] Обработка изменения голосового канала для участника {member.id}")

    guild_id = member.guild.id
    guild = member.guild
    channel_name = member.nick if member.nick else member.name
    find_message = None

    if before.channel and before.channel != after.channel:
        logger.info(f"Участник {member.id} покинул канал {before.channel.id} и перешёл в другой. Начинаем удаление старых find-сообщений.")
        await find_message_delete(before.channel.guild, member)
        temp_channels = load_temp_channels()
        if str(before.channel.id) in temp_channels:
            if len(before.channel.members) == 0:
                logger.info(f"Канал {before.channel.id} пуст, удаляем его.")
                await before.channel.delete()
                del temp_channels[str(before.channel.id)]
                save_temp_channels(temp_channels)

    if after.channel and after.channel != before.channel:
        voice_channel_id = after.channel.id
        logger.info(f"Участник {member.id} присоединился к каналу {voice_channel_id}")

        search_voice_channel_ids = await read_from_guild_settings_db(guild_id, "party_find_voice_channel_id")
        search_voice_channel_ids = [clean_channel_id(id_str) for id_str in search_voice_channel_ids]

        if voice_channel_id in search_voice_channel_ids:
            member_data = await read_member_data_from_db(member, 'voice_channel_name')
            if member_data:
                channel_name = member_data['data']
            if len(channel_name) > 100:
                channel_name = channel_name[:100]

            max_bitrate = after.channel.guild.bitrate_limit
            logger.info(f"Создаём временный канал с именем '{channel_name}' и битрейтом {max_bitrate} для участника {member.id}")
            temp_channel = await after.channel.guild.create_voice_channel(
                channel_name,
                bitrate=max_bitrate,
                category=after.channel.category
            )
            logger.info(f"Временный канал {temp_channel.id} создан.")

            overwrite = discord.PermissionOverwrite()
            overwrite.update(
                manage_channels=True,
                mute_members=True,
                move_members=True,
                manage_permissions=True
            )
            logger.info(f"Устанавливаем права для участника {member.id} на канале {temp_channel.id}.")
            await temp_channel.set_permissions(member, overwrite=overwrite)
            temp_channels = load_temp_channels()
            temp_channels[str(temp_channel.id)] = {"guild_id": guild_id}
            save_temp_channels(temp_channels)

            if member.voice and member.voice.channel:
                logger.info(f"Перемещаем участника {member.id} в новый канал {temp_channel.id}.")
                await member.move_to(temp_channel)

                button_data = {
                    "voice_id": f"id_{temp_channel.id}",
                    "creator_id": f"id_{member.id}"
                }
                logger.info(f"Отправляем сообщение управления на канале {temp_channel.id}.")
                control_message = await temp_channel.send(await get_phrase("Channel Management", guild_id))

                logger.info(f"Записываем данные кнопок для сообщения {control_message.id}.")
                await write_to_buttons_db(guild.id, control_message.id, "VoiceChannelControl", button_data, member.id)
                voice_button_view = VoiceChannelCcontrol(guild_id, member.id, temp_channel.id)
                await voice_button_view.initialize_buttons()
                await control_message.edit(view=voice_button_view)
            else:
                logger.info(f"Участник {member.id} не в голосовом канале после создания. Удаляем временный канал {temp_channel.id}.")
                await temp_channel.delete()
                return

            member_data = await read_member_data_from_db(member, 'party_find_mode')
            if member_data and member_data.get('data') == 'off':
                logger.info(f"Режим поиска компании отключён для участника {member.id}.")
            else:
                for activity in member.activities:
                    if activity.type == discord.ActivityType.playing:
                        role_name = activity.name
                        role = discord.utils.get(after.channel.guild.roles, name=role_name)
                        is_valid_game = is_game_valid(activity.name)
                        if role is None and is_valid_game:
                            random_color = random.randint(0, 0xFFFFFF)
                            logger.info(f"Создаём роль '{role_name}' для участника {member.id} с цветом {random_color}.")
                            role = await after.channel.guild.create_role(name=role_name, color=discord.Color(random_color))
                            await add_game_in_game_roles_channel(role, after.channel.guild)

                        if role not in member.roles and is_valid_game:
                            logger.info(f"Добавляем роль {role.id} участнику {member.id}.")
                            await member.add_roles(role)

                if member.voice and member.voice.channel:
                    for activity in member.activities:
                        if activity.type == discord.ActivityType.playing:
                            search_text_channel_ids = await read_from_guild_settings_db(guild_id, "party_find_text_channel_id")
                            search_text_channel_ids = [clean_channel_id(id_str) for id_str in search_text_channel_ids]

                            logger.info(f"Создаём инвайт для канала {temp_channel.id}.")
                            invite = await temp_channel.create_invite(max_age=3600, max_uses=99)

                            for text_channel_id in search_text_channel_ids:
                                text_channel = member.guild.get_channel(text_channel_id)
                                if text_channel:
                                    find_message = await text_channel.send(
                                        content=f"{member.mention} {await get_phrase('looking for a company', guild)} "
                                                f"{temp_channel.mention}.\n"
                                                f"## <@&{role.id}>"
                                    )

                                    invite_data = {"invite": invite.url}
                                    logger.info(f"Записываем данные для кнопки присоединения для сообщения {find_message.id} в канале {text_channel.id}.")
                                    await write_to_buttons_db(guild.id, find_message.id, "JoinButton", invite_data, member.id)
                                    join_button_view = JoinButton(invite, guild_id, activity, member.id)
                                    await join_button_view.initialize_buttons()
                                    await find_message.edit(view=join_button_view)
                                    break

                            asyncio.create_task(check_member_in_channel(member, temp_channel, find_message, invite))
    logger.info(f"[END] Завершена обработка участника {member.id}")





async def find_message_delete(guild, member):
    try:
        search_text_channel_ids = await read_from_guild_settings_db(guild.id, "party_find_text_channel_id")
        search_text_channel_ids = [clean_channel_id(id_str) for id_str in search_text_channel_ids]

        current_voice_channel = member.voice.channel if member.voice else None

        for text_channel_id in search_text_channel_ids:
            text_channel = member.guild.get_channel(text_channel_id)
            if text_channel:
                async for message in text_channel.history(limit=20):
                    if str(member.id) in message.content:
                        if current_voice_channel and str(current_voice_channel.id) in message.content:
                            logger.debug("Channel mentioned in message, skipping delete")
                        else:
                            logger.debug("DELETE find message")
                            await message.delete()

    except discord.NotFound:
        pass


async def check_member_in_channel(member, temp_channel, find_message, invite):
    while True:
        await asyncio.sleep(30)

        if member not in temp_channel.members:
            await find_message_delete(temp_channel.guild, member)

            break