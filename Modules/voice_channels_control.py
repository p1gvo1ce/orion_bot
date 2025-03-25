import os
import json
import discord
import random
import asyncio
from datetime import datetime, timedelta
import random
import string

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

# Функция для использования резервного канала (План Б)
async def use_reserved_channel(bot, guild, visible_category, new_channel_name, overwrites, member):
    # Резервная категория с ID 1353976761234362369
    reserved_category = guild.get_channel(1353976761234362369)
    if not reserved_category:
        # Если не найдено – создаём скрытую категорию
        reserved_category = await guild.create_category(
            "Reserved Channels",
            overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        )
    # Ищем свободный голосовой канал в резервной категории
    reserved_channel = None
    for channel in guild.channels:
        if channel.category_id == reserved_category.id and isinstance(channel, discord.VoiceChannel):
            reserved_channel = channel
            break
    if not reserved_channel:
        reserved_channel = await guild.create_voice_channel(
            "ReservedChannel",
            category=reserved_category,
            overwrites=overwrites
        )
    # Засекаем время обновления: переименование, синхронизация пермишенов, перемещение в видимую категорию
    update_start = datetime.utcnow()
    try:
        await reserved_channel.edit(name=new_channel_name, overwrites=overwrites, category=visible_category)
    except Exception as e:
        print("Ошибка при обновлении резервного канала:", e)
    update_end = datetime.utcnow()
    update_interval = (update_end - update_start).total_seconds()
    # Перемещаем участника в этот канал
    try:
        await member.move_to(reserved_channel)
    except Exception as e:
        print("Ошибка перемещения участника в резервный канал:", e)
    return reserved_channel, update_interval

# Если по плану A вдруг канал появится – удаляем его, чтобы не плодить лишние
async def cleanup_plan_a_channel(guild, visible_category, new_channel_name, fallback_channel):
    await asyncio.sleep(10)  # даём время, чтобы план A канал, если и создался, успел появиться
    for channel in guild.channels:
        if channel.category_id == visible_category.id and channel.name == new_channel_name:
            if channel.id != fallback_channel.id:
                try:
                    await channel.delete()
                    print(f"[CLEANUP] Удалён лишний канал {channel.id}")
                except Exception as e:
                    print("Ошибка удаления лишнего канала:", e)

async def find_party_controller(member, before, after):

    logger = get_logger()
    logger.info(f"[START] Обработка изменения голосового канала для участника {member.id}")

    guild_id = member.guild.id
    guild = member.guild
    # Изначально имя канала – имя участника (или его ник)
    channel_name = member.nick if member.nick else member.name

    # Если участник покинул предыдущий канал, удаляем временные сообщения и канал
    if before.channel and before.channel != after.channel:
        logger.info(f"Участник {member.id} покинул канал {before.channel.id} и перешёл в другой. Удаляем старые find-сообщения.")
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

            creation_start = datetime.utcnow()
            plan_used = None
            new_channel = None
            creation_interval = None

            try:
                # План A: пытаемся создать канал с таймаутом 2 секунды
                new_channel = await asyncio.wait_for(
                    after.channel.guild.create_voice_channel(
                        channel_name,
                        bitrate=max_bitrate,
                        category=after.channel.category
                    ),
                    timeout=2
                )
                creation_end = datetime.utcnow()
                creation_interval = (creation_end - creation_start).total_seconds()
                plan_used = "A"
                logger.info(f"План A: создан канал {new_channel.id} за {creation_interval:.3f} секунд.")
            except asyncio.TimeoutError:
                creation_end = datetime.utcnow()
                creation_interval = (creation_end - creation_start).total_seconds()
                plan_used = "B"
                logger.info("Время создания канала превысило 2 секунды, переключаемся на план B (резервный канал).")
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.get_role(923183831094284318): discord.PermissionOverwrite(view_channel=True)
                }
                new_channel, fallback_interval = await use_reserved_channel(bot, guild, after.channel.category, channel_name, overwrites, member)
                creation_interval = fallback_interval
                # Запускаем задачу очистки, если вдруг канал по плану A появится позже
                asyncio.create_task(cleanup_plan_a_channel(guild, after.channel.category, channel_name, new_channel))
            except Exception as e:
                creation_end = datetime.utcnow()
                creation_interval = (creation_end - creation_start).total_seconds()
                plan_used = "Error"
                logger.info(f"Ошибка при создании канала: {e}")

            # Сохраняем данные временного канала
            temp_channels = load_temp_channels()
            temp_channels[str(new_channel.id)] = {"guild_id": guild_id}
            save_temp_channels(temp_channels)

            if member.voice and member.voice.channel:
                logger.info(f"Перемещаем участника {member.id} в канал {new_channel.id}.")
                try:
                    await member.move_to(new_channel)
                except Exception as e:
                    logger.info(f"Ошибка перемещения участника: {e}")

                button_data = {
                    "voice_id": f"id_{new_channel.id}",
                    "creator_id": f"id_{member.id}"
                }
                logger.info(f"Отправляем сообщение управления на канале {new_channel.id}.")
                control_message = await new_channel.send(await get_phrase("Channel Management", guild_id))
                logger.info(f"Записываем данные кнопок для сообщения {control_message.id}.")
                await write_to_buttons_db(guild.id, control_message.id, "VoiceChannelControl", button_data, member.id)
                voice_button_view = VoiceChannelCcontrol(guild_id, member.id, new_channel.id)
                await voice_button_view.initialize_buttons()
                await control_message.edit(view=voice_button_view)
            else:
                logger.info(f"Участник {member.id} не в голосовом канале после создания. Удаляем канал {new_channel.id}.")
                await new_channel.delete()
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
                            logger.info(f"Создаём инвайт для канала {new_channel.id}.")
                            invite = await new_channel.create_invite(max_age=3600, max_uses=99)
                            for text_channel_id in search_text_channel_ids:
                                text_channel = member.guild.get_channel(text_channel_id)
                                if text_channel:
                                    find_message = await text_channel.send(
                                        content=f"{member.mention} {await get_phrase('looking for a company', guild)} {new_channel.mention}.\n## <@&{role.id}>"
                                    )
                                    invite_data = {"invite": invite.url}
                                    logger.info(f"Записываем данные для кнопки присоединения для сообщения {find_message.id} в канале {text_channel.id}.")
                                    await write_to_buttons_db(guild.id, find_message.id, "JoinButton", invite_data, member.id)
                                    join_button_view = JoinButton(invite, guild_id, activity, member.id)
                                    await join_button_view.initialize_buttons()
                                    await find_message.edit(view=join_button_view)
                                    break
                            asyncio.create_task(check_member_in_channel(member, new_channel, find_message, invite))
    logger.info(f"[END] Завершена обработка участника {member.id}")

    # Формируем итоговый embed-отчёт
    creation_interval = (creation_end - creation_start).total_seconds() if creation_start and creation_end else 0


    report_embed = discord.Embed(title="Private Voice Update Report")
    report_embed.add_field(name="План", value=f"План {plan_used}", inline=False)
    report_embed.add_field(name="Интервал создания/обновления", value=f"{creation_interval:.3f} секунд", inline=False)
    report_embed.timestamp = datetime.utcnow()

    report_channel = guild.get_channel(1353656805116477530)
    if report_channel:
        try:
            await report_channel.send(embed=report_embed)
        except Exception as e:
            logger.info(f"Ошибка отправки отчёта: {e}")
    else:
        logger.info("Текстовый канал для отчётов не найден.")





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