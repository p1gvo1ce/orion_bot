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
    update_logs = {}
    # Получаем резервную категорию (ID: 1353976761234362369)
    reserved_category = guild.get_channel(1353976761234362369)
    if not reserved_category:
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
    # Засекаем время начала обновления
    update_logs['update_start'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    try:
        # Перемещаем канал в видимую категорию
        await reserved_channel.edit(category=visible_category)
        # Синхронизируем права канала с правами новой категории
        await reserved_channel.edit(sync_permissions=True)
        # Обновляем имя канала
        await reserved_channel.edit(name=new_channel_name)
        # После синхронизации получаем копию прав категории
        current_overwrites = visible_category.overwrites.copy()
        # Добавляем для владельца (member) дополнительные права
        current_overwrites[member] = discord.PermissionOverwrite(
            manage_channels=True,
            mute_members=True,
            deafen_members=True,
            move_members=True,
            manage_permissions=True
        )
        await reserved_channel.edit(overwrites=current_overwrites)
    except Exception as e:
        print("Ошибка при обновлении резервного канала:", e)
    update_logs['update_end'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    # Перемещаем участника в этот канал
    try:
        await member.move_to(reserved_channel)
    except Exception as e:
        print("Ошибка перемещения участника в резервный канал:", e)
    update_logs['moved_reserved'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    update_interval = (datetime.strptime(update_logs['update_end'], '%Y-%m-%d %H:%M:%S.%f') -
                       datetime.strptime(update_logs['update_start'], '%Y-%m-%d %H:%M:%S.%f')).total_seconds()
    return reserved_channel, update_interval, update_logs

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

TESTING = False  # Установи True для отладки, чтобы форсировать оба плана по очереди
TEST_PLAN_TOGGLE = 0  # Будет чередоваться: четное значение -> план A, нечетное -> план B

async def find_party_controller(member, before, after):
    global TESTING, TEST_PLAN_TOGGLE
    logger = get_logger()
    connection_time = datetime.utcnow()
    logger.info(
        f"[START] [{connection_time.strftime('%Y-%m-%d %H:%M:%S.%f')}] Обработка изменения голосового канала для участника {member.id}")

    channel_name = member.nick if member.nick else member.name

    if before.channel and before.channel != after.channel:
        logger.info(
            f"[LEAVE] Пользователь {member.id} покинул канал {before.channel.id} в {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}, удаляем старые find-сообщения.")
        await find_message_delete(before.channel.guild, member)
        temp_channels = load_temp_channels()
        if str(before.channel.id) in temp_channels:
            if len(before.channel.members) == 0:
                logger.info(
                    f"[CLEANUP] Канал {before.channel.id} пуст, удаляем его в {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}.")
                await before.channel.delete()
                del temp_channels[str(before.channel.id)]
                save_temp_channels(temp_channels)

    # Инициализация переменных этапов
    creation_start = None
    creation_end = None
    movement_start = None
    movement_end = None
    movement_interval = 0
    creation_interval = 0
    plan_used = None

    if after.channel and after.channel != before.channel:
        connection_time = datetime.utcnow()
        logger.info(
            f"[CONNECT] Пользователь {member.id} подключился к каналу {after.channel.id} в {connection_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
        guild_id = member.guild.id
        guild = member.guild
        voice_channel_id = after.channel.id

        search_voice_channel_ids = await read_from_guild_settings_db(guild_id, "party_find_voice_channel_id")
        search_voice_channel_ids = [clean_channel_id(id_str) for id_str in search_voice_channel_ids]

        if voice_channel_id in search_voice_channel_ids:
            member_data = await read_member_data_from_db(member, 'voice_channel_name')
            if member_data:
                channel_name = member_data['data']
            if len(channel_name) > 100:
                channel_name = channel_name[:100]

            max_bitrate = after.channel.guild.bitrate_limit
            logger.info(
                f"[CREATE] Создаем временный канал с именем '{channel_name}' и битрейтом {max_bitrate} для пользователя {member.id} в {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            creation_start = datetime.utcnow()
            plan_used = None
            new_channel = None
            creation_interval = None
            plan_logs = {}

            global TESTING, TEST_PLAN_TOGGLE
            if TESTING:
                forced_plan = "A" if (TEST_PLAN_TOGGLE % 2 == 0) else "B"
                TEST_PLAN_TOGGLE += 1
            else:
                forced_plan = None

            if forced_plan == "A" or (forced_plan is None):
                try:
                    new_channel = await asyncio.wait_for(
                        guild.create_voice_channel(
                            channel_name,
                            bitrate=max_bitrate,
                            category=after.channel.category
                        ),
                        timeout=2
                    )
                    creation_end = datetime.utcnow()
                    creation_interval = (creation_end - creation_start).total_seconds()
                    plan_used = "A"
                    logger.info(
                        f"[PLAN A] Канал {new_channel.id} создан в {creation_end.strftime('%Y-%m-%d %H:%M:%S.%f')} за {creation_interval:.3f} секунд.")
                    # Синхронизируем права канала с правами категории и добавляем права для владельца
                    try:
                        await new_channel.edit(sync_permissions=True)
                        # Берем права из видимой категории
                        visible_category = after.channel.category
                        base_overwrites = visible_category.overwrites.copy() if visible_category.overwrites else {}
                        base_overwrites.update({
                            member: discord.PermissionOverwrite(
                                manage_channels=True,
                                mute_members=True,
                                deafen_members=True,
                                move_members=True,
                                manage_permissions=True
                            )
                        })
                        await new_channel.edit(overwrites=base_overwrites)
                        logger.info(f"[PLAN A] Права для владельца добавлены для канала {new_channel.id}.")
                    except Exception as e:
                        logger.info(f"[PLAN A] Ошибка при установке прав владельца: {e}")
                except asyncio.TimeoutError:
                    creation_end = datetime.utcnow()
                    creation_interval = (creation_end - creation_start).total_seconds()
                    plan_used = "B"
                    logger.info(
                        f"[PLAN A Timeout] Создание канала превысило 2 секунды в {creation_end.strftime('%Y-%m-%d %H:%M:%S.%f')}, переключаемся на план B.")
                except Exception as e:
                    creation_end = datetime.utcnow()
                    creation_interval = (creation_end - creation_start).total_seconds()
                    plan_used = "Error"
                    logger.info(
                        f"[PLAN A Error] Ошибка создания канала: {e} в {creation_end.strftime('%Y-%m-%d %H:%M:%S.%f')}")

            if plan_used == "B" or forced_plan == "B":
                fallback_trigger_time = datetime.utcnow()
                logger.info(
                    f"[PLAN B] Начало работы плана B в {fallback_trigger_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.get_role(923183831094284318): discord.PermissionOverwrite(view_channel=True)
                }
                new_channel, fallback_interval, plan_b_logs = await use_reserved_channel(bot, guild,
                                                                                         after.channel.category,
                                                                                         channel_name, overwrites,
                                                                                         member)
                creation_end = datetime.utcnow()
                creation_interval = fallback_interval
                plan_logs.update(plan_b_logs)
                plan_used = "B"
                logger.info(f"[PLAN B] Резервный канал {new_channel.id} обновлен, данные: {plan_b_logs}")
                asyncio.create_task(cleanup_plan_a_channel(guild, after.channel.category, channel_name, new_channel))

            if new_channel is None:
                logger.info(f"[ERROR] new_channel не создан для пользователя {member.id}")
                return

            temp_channels = load_temp_channels()
            temp_channels[str(new_channel.id)] = {"guild_id": guild_id}
            save_temp_channels(temp_channels)

            movement_start = datetime.utcnow()
            if member.voice and member.voice.channel:
                logger.info(
                    f"[MOVE] Перемещаем участника {member.id} в канал {new_channel.id} в {movement_start.strftime('%Y-%m-%d %H:%M:%S.%f')}.")
                try:
                    await member.move_to(new_channel)
                except Exception as e:
                    logger.info(f"[MOVE ERROR] Ошибка перемещения участника: {e}")
            movement_end = datetime.utcnow()
            movement_interval = (movement_end - movement_start).total_seconds()

            button_data = {
                "voice_id": f"id_{new_channel.id}",
                "creator_id": f"id_{member.id}"
            }
            logger.info(
                f"[BUTTON] Отправляем сообщение управления на канале {new_channel.id} в {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}.")
            control_message = await new_channel.send(await get_phrase("Channel Management", guild_id))
            logger.info(
                f"[BUTTON] Сообщение управления {control_message.id} отправлено в {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}.")
            await write_to_buttons_db(guild.id, control_message.id, "VoiceChannelControl", button_data, member.id)
            voice_button_view = VoiceChannelCcontrol(guild_id, member.id, new_channel.id)
            await voice_button_view.initialize_buttons()
            await control_message.edit(view=voice_button_view)

            member_data = await read_member_data_from_db(member, 'party_find_mode')
            if member_data and member_data.get('data') == 'off':
                logger.info(f"[MODE] Режим поиска компании отключён для участника {member.id}.")
            else:
                for activity in member.activities:
                    if activity.type == discord.ActivityType.playing:
                        role_name = activity.name
                        role = discord.utils.get(after.channel.guild.roles, name=role_name)
                        is_valid_game = is_game_valid(activity.name)
                        if role is None and is_valid_game:
                            random_color = random.randint(0, 0xFFFFFF)
                            logger.info(
                                f"[ROLE] Создаем роль '{role_name}' для участника {member.id} с цветом {random_color}.")
                            role = await after.channel.guild.create_role(name=role_name,
                                                                         color=discord.Color(random_color))
                            await add_game_in_game_roles_channel(role, after.channel.guild)
                        if role not in member.roles and is_valid_game:
                            logger.info(f"[ROLE] Добавляем роль {role.id} участнику {member.id}.")
                            await member.add_roles(role)
                if member.voice and member.voice.channel:
                    for activity in member.activities:
                        if activity.type == discord.ActivityType.playing:
                            search_text_channel_ids = await read_from_guild_settings_db(guild_id,
                                                                                        "party_find_text_channel_id")
                            search_text_channel_ids = [clean_channel_id(id_str) for id_str in search_text_channel_ids]
                            logger.info(
                                f"[INVITE] Создаем инвайт для канала {new_channel.id} в {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}.")
                            invite = await new_channel.create_invite(max_age=3600, max_uses=99)
                            for text_channel_id in search_text_channel_ids:
                                text_channel = member.guild.get_channel(text_channel_id)
                                if text_channel:
                                    find_message = await text_channel.send(
                                        content=f"{member.mention} {await get_phrase('looking for a company', guild)} {new_channel.mention}.\n## <@&{role.id}>"
                                    )
                                    invite_data = {"invite": invite.url}
                                    logger.info(
                                        f"[INVITE] Записываем данные для кнопки присоединения для сообщения {find_message.id} в канале {text_channel.id} в {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}.")
                                    await write_to_buttons_db(guild.id, find_message.id, "JoinButton", invite_data,
                                                              member.id)
                                    join_button_view = JoinButton(invite, guild_id, activity, member.id)
                                    await join_button_view.initialize_buttons()
                                    await find_message.edit(view=join_button_view)
                                    break
                            asyncio.create_task(check_member_in_channel(member, new_channel, find_message, invite))
    logger.info(
        f"[END] Завершена обработка участника {member.id} в {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}")

    total_interval = 0
    if creation_start is not None and creation_end is not None:
        total_interval += (creation_end - creation_start).total_seconds()
    total_interval += movement_interval

    if total_interval >= 5:
        embed_color = "#8B0000"
    elif total_interval <= 1:
        embed_color = "#00FF7F"
    else:
        embed_color = "#20B2AA"

    report_embed = discord.Embed(title="Private Voice Update Report", color=discord.Color.from_str(embed_color))
    report_embed.add_field(name="План", value=f"План {plan_used}", inline=False)
    report_embed.add_field(name="Время подключения", value=connection_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                           inline=False)
    report_embed.add_field(name="Начало создания",
                           value=creation_start.strftime('%Y-%m-%d %H:%M:%S.%f') if creation_start else "нет данных",
                           inline=False)
    report_embed.add_field(name="Окончание создания/обновления",
                           value=creation_end.strftime('%Y-%m-%d %H:%M:%S.%f') if creation_end else "нет данных",
                           inline=False)
    report_embed.add_field(name="Интервал создания/обновления",
                           value=f"{creation_interval:.3f} секунд" if creation_interval is not None else "нет данных",
                           inline=False)
    report_embed.add_field(name="Время перемещения",
                           value=movement_end.strftime('%Y-%m-%d %H:%M:%S.%f') if movement_end else "нет данных",
                           inline=False)
    report_embed.add_field(name="Интервал перемещения", value=f"{movement_interval:.3f} секунд", inline=False)
    report_embed.add_field(name="Суммарное время (создание+перемещение)", value=f"{total_interval:.3f} секунд",
                           inline=False)
    if plan_used == "B":
        report_embed.add_field(name="План B: Начало обновления", value=plan_logs.get('update_start', 'нет данных'),
                               inline=False)
        report_embed.add_field(name="План B: Окончание обновления", value=plan_logs.get('update_end', 'нет данных'),
                               inline=False)
        report_embed.add_field(name="План B: Перемещение в резервный канал",
                               value=plan_logs.get('moved_reserved', 'нет данных'), inline=False)
    report_embed.timestamp = datetime.utcnow()

    report_channel = guild.get_channel(1353656805116477530)

    # В конце функции, перед формированием embed, делаем проверку:
    if plan_used is None or new_channel is None:
        # Значит, мы не делали фактическое создание/обновление канала
        logger.info("Пропускаем отправку embed, т.к. не было создания канала.")
        return

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