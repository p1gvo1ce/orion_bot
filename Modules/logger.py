import json
import discord
from datetime import datetime, timedelta

from Modules.db_control import log_event_to_db, read_from_guild_settings_db
from utils import clean_channel_id
from Modules.phrases import get_phrase

async def log_new_message(message):
    if message.author.bot:
        return
    guild_id = message.guild.id
    is_member = isinstance(message.author, discord.Member)

    # Инициализация переменной для времени
    formatted_time = datetime.utcnow().isoformat()  # По умолчанию текущее время в UTC

    # Проверяем, включено ли логирование
    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        # Получаем ID канала для логирования
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        # Получаем смещение UTC
        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = message.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
                    description = (
                        f"**{await get_phrase("New Message", message.guild)}**\n"
                        f"**{await get_phrase("Author", message.guild)}**: {message.author.name}#{message.author.discriminator} "
                        f"<@{message.author.id}>\n"
                        f"**{await get_phrase("Content", message.guild)}**: ``` {message.content} ```\n"
                        f"**{await get_phrase("Channel", message.guild)}**: {message.channel.name} <#{message.channel.id}>\n"
                        f"**{await get_phrase("Created At", message.guild)}**: {formatted_time}\n"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    # Логируем в базу данных
    data = {
        "message": {
            "activity": str(message.activity),
            "application": str(message.application),
            "application_id": str(message.application_id),
            "attachments": str([attachment.to_dict() for attachment in message.attachments]),
            "author": {
                "accent_color": str(message.author.accent_color),
                "avatar": str(message.author.avatar),
                "discriminator": str(message.author.discriminator),
                "id": str(message.author.id),
                "mention": str(message.author.mention),
                "name": str(message.author.name),
                "nick": str(message.author.nick if is_member else None),
            },
            "channel": {
                "category": str(message.channel.category),
                "id": str(message.channel.id),
                "name": str(message.channel.name),
                "type": str(message.channel.type),
            },
            "content": str(message.content),
            "created_at": str(formatted_time),  # Используем отформатированное время
            "edited_at": str(message.edited_at.isoformat() if message.edited_at else None),
        }
    }
    await log_event_to_db(guild_id, "new_message", data)


async def log_deleted_message(message):
    # Игнорируем сообщения, отправленные ботом
    if message.author.bot:
        return

    guild_id = message.guild.id
    formatted_time = datetime.utcnow().isoformat()  # По умолчанию текущее время в UTC

    # Проверяем, включено ли логирование
    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        # Получаем ID канала для логирования
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        # Получаем смещение UTC
        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        # Если каналы для логирования найдены
        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = message.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#FF4500"))  # Цвет для удаленного сообщения
                    description = (
                        f"**{await get_phrase('Deleted Message', message.guild)}**\n"
                        f"**{await get_phrase('Author', message.guild)}**: {message.author.name}#{message.author.discriminator} "
                        f"<@{message.author.id}>\n"
                        f"**{await get_phrase('Content', message.guild)}**: ``` {message.content} ```\n"
                        f"**{await get_phrase('Channel', message.guild)}**: {message.channel.name} <#{message.channel.id}>\n"
                        f"**{await get_phrase('Deleted At', message.guild)}**: {formatted_time}\n"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    # Логируем в базу данных
    data = {
        "message": {
            "id": str(message.id),
            "channel_id": str(message.channel.id),
            "content": str(message.content),
            "deleted_at": str(formatted_time),  # Используем отформатированное время
            "author": {
                "id": str(message.author.id),
                "name": str(message.author.name),
                "discriminator": str(message.author.discriminator),
                "avatar": str(message.author.avatar),
            },
            "channel": {
                "id": str(message.channel.id),
                "name": str(message.channel.name),
                "type": str(message.channel.type),
            }
        }
    }
    await log_event_to_db(guild_id, "deleted_message", data)


async def log_edited_message(before, after):
    # Игнорируем изменения сообщений, отправленных ботом
    if after.author.bot:
        return
    guild_id = after.guild.id
    is_member = isinstance(after.author, discord.Member)

    # Инициализация переменной для времени
    formatted_time = datetime.utcnow().isoformat()  # По умолчанию текущее время в UTC

    # Проверяем, включено ли логирование
    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        # Получаем ID канала для логирования
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        # Получаем смещение UTC
        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        # Если каналы для логирования найдены
        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = after.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#FFA500"))  # Цвет для отредактированных сообщений
                    description = (
                        f"**{await get_phrase('Message Edited', after.guild)}**\n"
                        f"**{await get_phrase('Author', after.guild)}**: {after.author.name}#{after.author.discriminator} "
                        f"<@{after.author.id}>\n"
                        f"**{await get_phrase('Content Before', after.guild)}**: ``` {before.content} ```\n"
                        f"**{await get_phrase('Content After', after.guild)}**: ``` {after.content} ```\n"
                        f"**{await get_phrase('Channel', after.guild)}**: {after.channel.name} <#{after.channel.id}>\n"
                        f"**{await get_phrase('Edited At', after.guild)}**: {formatted_time}\n"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    # Логируем в базу данных
    data = {
        "message": {
            "id": str(after.id),
            "content_before": str(before.content),
            "content_after": str(after.content),
            "edited_at": str(formatted_time),  # Используем отформатированное время
        },
        "author": {
            "id": str(after.author.id),
            "name": str(after.author.name),
            "nick": str(after.author.nick if is_member else None),
        },
        "channel": {
            "id": str(after.channel.id),
            "name": str(after.channel.name),
        }
    }
    await log_event_to_db(guild_id, "edited_message", data)
