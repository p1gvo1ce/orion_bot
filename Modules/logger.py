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

    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

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
    if message.author.bot:
        return

    guild_id = message.guild.id
    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = message.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#FF4500"))
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

    data = {
        "message": {
            "id": str(message.id),
            "channel_id": str(message.channel.id),
            "content": str(message.content),
            "deleted_at": str(formatted_time),
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
    if after.author.bot:
        return
    guild_id = after.guild.id
    is_member = isinstance(after.author, discord.Member)

    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = after.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#FFA500"))
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

    data = {
        "message": {
            "id": str(after.id),
            "content_before": str(before.content),
            "content_after": str(after.content),
            "edited_at": str(formatted_time),
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

async def log_joined_member(member, inviter_id, invite_code):
    guild_id = member.guild.id
    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = member.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#00FA9A"))
                    description = (
                        f"**{await get_phrase('New Member Joined', member.guild)}**\n"
                        f"**{await get_phrase('Member', member.guild)}**: {member.name}#{member.discriminator} "
                        f"<@{member.id}>\n"
                        f"**{await get_phrase('Invited by', member.guild)}**: <@{inviter_id}>\n"
                        f"**{await get_phrase('Invite Code', member.guild)}**: `{invite_code}`\n"
                        f"**{await get_phrase('Joined At', member.guild)}**: {formatted_time}\n"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    data = {
        "member": {
            "id": str(member.id),
            "name": str(member.name),
            "discriminator": str(member.discriminator),
            "avatar": str(member.avatar),
            "joined_at": str(formatted_time),
            "inviter": {
                "id": str(inviter_id),
            },
            "invite_code": invite_code
        }
    }
    await log_event_to_db(guild_id, "member_joined", data)

async def log_member_left(member):
    if member.bot:
        return

    guild_id = member.guild.id
    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = member.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#8B0000"))
                    description = (
                        f"**{await get_phrase('Member Left', member.guild)}**\n"
                        f"**{await get_phrase('Name', member.guild)}**: {member.name}#{member.discriminator} "
                        f"<@{member.id}>\n"
                        f"**{await get_phrase('Left At', member.guild)}**: {formatted_time}\n"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    data = {
        "member": {
            "id": str(member.id),
            "name": str(member.name),
            "discriminator": str(member.discriminator),
            "avatar": str(member.avatar),
            "left_at": str(formatted_time),
        }
    }
    await log_event_to_db(guild_id, "member_left", data)

async def log_member_muted(member, reason=None, duration=None):
    if member.bot:
        return

    guild_id = member.guild.id
    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = member.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#778899"))
                    description = (
                        f"**{await get_phrase('Member Muted', member.guild)}**\n"
                        f"**{await get_phrase('Member', member.guild)}**: {member.name}#{member.discriminator} "
                        f"<@{member.id}>\n"
                        f"**{await get_phrase('Muted At', member.guild)}**: {formatted_time}\n"
                        f"**{await get_phrase('Reason', member.guild)}**: {reason or await get_phrase('No reason provided', member.guild)}\n"
                        f"**{await get_phrase('Duration', member.guild)}**: {duration or await get_phrase('Indefinite', member.guild)}"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    data = {
        "member": {
            "id": str(member.id),
            "name": str(member.name),
            "discriminator": str(member.discriminator),
            "muted_at": str(formatted_time),
            "reason": str(reason),
            "duration": str(duration),
        }
    }
    await log_event_to_db(guild_id, "member_muted", data)

async def log_member_unmuted(member, reason=None):
    if member.bot:
        return

    guild_id = member.guild.id
    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = member.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#FFFF00"))
                    description = (
                        f"**{await get_phrase('Member Unmuted', member.guild)}**\n"
                        f"**{await get_phrase('Member', member.guild)}**: {member.name}#{member.discriminator} "
                        f"<@{member.id}>\n"
                        f"**{await get_phrase('Unmuted At', member.guild)}**: {formatted_time}\n"
                        f"**{await get_phrase('Reason', member.guild)}**: {reason or await get_phrase('No reason provided', member.guild)}"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    data = {
        "member": {
            "id": str(member.id),
            "name": str(member.name),
            "discriminator": str(member.discriminator),
            "unmuted_at": str(formatted_time),
            "reason": str(reason),
        }
    }
    await log_event_to_db(guild_id, "member_unmuted", data)


async def log_member_banned(member, reason=None):
    if member.bot:
        return

    guild_id = member.guild.id
    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = member.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#B22222"))
                    description = (
                        f"**{await get_phrase('Member Banned', member.guild)}**\n"
                        f"**{await get_phrase('Member', member.guild)}**: {member.name}#{member.discriminator} "
                        f"<@{member.id}>\n"
                        f"**{await get_phrase('Banned At', member.guild)}**: {formatted_time}\n"
                        f"**{await get_phrase('Reason', member.guild)}**: {reason or await get_phrase('No reason provided', member.guild)}"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    data = {
        "member": {
            "id": str(member.id),
            "name": str(member.name),
            "discriminator": str(member.discriminator),
            "banned_at": str(formatted_time),
            "reason": str(reason),
        }
    }
    await log_event_to_db(guild_id, "member_banned", data)

async def log_voice_state_update(member, before, after):
    guild_id = member.guild.id
    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        event_description = None
        if before.channel is None and after.channel is not None:
            # Присоединение к голосовому каналу
            event_description = f"**{await get_phrase('Joined Voice Channel', member.guild)}**"
            event_type = "voice_joined"
        elif before.channel is not None and after.channel is None:
            # Отключение от голосового канала
            event_description = f"**{await get_phrase('Left Voice Channel', member.guild)}**"
            event_type = "voice_left"
        elif before.channel != after.channel:
            # Переход между голосовыми каналами
            event_description = f"**{await get_phrase('Switched Voice Channels', member.guild)}**"
            event_type = "voice_switched"
        elif before.self_mute != after.self_mute:
            # Включение/выключение микрофона
            if after.self_mute:
                event_description = f"**{await get_phrase('Muted Microphone', member.guild)}**"
            else:
                event_description = f"**{await get_phrase('Unmuted Microphone', member.guild)}**"
            event_type = "voice_mute"
        elif before.self_deaf != after.self_deaf:
            # Включение/выключение звука
            if after.self_deaf:
                event_description = f"**{await get_phrase('Deafened', member.guild)}**"
            else:
                event_description = f"**{await get_phrase('Undeafened', member.guild)}**"
            event_type = "voice_deaf"

        if event_description and log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = member.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(color=discord.Color.from_str("#4682B4"))
                    description = (
                        f"**{await get_phrase('Member', member.guild)}**: {member.name}#{member.discriminator} "
                        f"<@{member.id}>\n"
                        f"{event_description}\n"
                        f"**{await get_phrase('Voice Channel', member.guild)}**: {after.channel.name if after.channel else before.channel.name}\n"
                        f"**{await get_phrase('Occurred At', member.guild)}**: {formatted_time}\n"
                    )
                    embed.description = description
                    await log_channel.send(embed=embed)

    data = {
        "member": {
            "id": str(member.id),
            "name": str(member.name),
            "discriminator": str(member.discriminator),
            "avatar": str(member.avatar),
        },
        "event": {
            "type": event_type,
            "channel": {
                "id": str(after.channel.id if after.channel else before.channel.id),
                "name": str(after.channel.name if after.channel else before.channel.name),
            },
            "occurred_at": formatted_time
        }
    }
    await log_event_to_db(guild_id, event_type, data)

async def log_role_channel_event(event_type, before=None, after=None, guild=None):
    if guild is None:
        return

    guild_id = guild.id
    formatted_time = datetime.utcnow().isoformat()

    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if logging_status and logging_status[0] == 'on':
        log_channel_ids = await read_from_guild_settings_db(guild_id, "log_channel_id")
        log_channel_ids = [clean_channel_id(id_str) for id_str in log_channel_ids]

        utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
        utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

        utc_time = datetime.utcnow() + timedelta(hours=utc_offset)
        formatted_time = utc_time.isoformat()

        if log_channel_ids:
            for log_channel_id in log_channel_ids:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    if event_type == "role_created":
                        role = after
                        description = (
                            f"**{await get_phrase('Role Created', guild)}**\n"
                            f"**{await get_phrase('Role Name', guild)}**: {role.name}\n"
                            f"**{await get_phrase('Role ID', guild)}**: {role.id}\n"
                            f"**{await get_phrase('Created At', guild)}**: {formatted_time}\n"
                        )
                    elif event_type == "role_updated":
                        description = (
                            f"**{await get_phrase('Role Updated', guild)}**\n"
                            f"**{await get_phrase('Before', guild)}**: {before.name} (ID: {before.id})\n"
                            f"**{await get_phrase('After', guild)}**: {after.name} (ID: {after.id})\n"
                            f"**{await get_phrase('Updated At', guild)}**: {formatted_time}\n"
                        )
                    elif event_type == "role_deleted":
                        description = (
                            f"**{await get_phrase('Role Deleted', guild)}**\n"
                            f"**{await get_phrase('Role Name', guild)}**: {before.name}\n"
                            f"**{await get_phrase('Role ID', guild)}**: {before.id}\n"
                            f"**{await get_phrase('Deleted At', guild)}**: {formatted_time}\n"
                        )
                    elif event_type == "channel_created":
                        channel = after
                        description = (
                            f"**{await get_phrase('Channel Created', guild)}**\n"
                            f"**{await get_phrase('Channel Name', guild)}**: {channel.name}\n"
                            f"**{await get_phrase('Channel ID', guild)}**: {channel.id}\n"
                            f"**{await get_phrase('Created At', guild)}**: {formatted_time}\n"
                        )
                    elif event_type == "channel_updated":
                        description = (
                            f"**{await get_phrase('Channel Updated', guild)}**\n"
                            f"**{await get_phrase('Before', guild)}**: {before.name} (ID: {before.id})\n"
                            f"**{await get_phrase('After', guild)}**: {after.name} (ID: {after.id})\n"
                            f"**{await get_phrase('Updated At', guild)}**: {formatted_time}\n"
                        )
                    elif event_type == "channel_deleted":
                        description = (
                            f"**{await get_phrase('Channel Deleted', guild)}**\n"
                            f"**{await get_phrase('Channel Name', guild)}**: {before.name}\n"
                            f"**{await get_phrase('Channel ID', guild)}**: {before.id}\n"
                            f"**{await get_phrase('Deleted At', guild)}**: {formatted_time}\n"
                        )

                    embed = discord.Embed(color=discord.Color.from_str("#6B8E23"))
                    embed.description = description
                    await log_channel.send(embed=embed)

    data = {
        "event_type": event_type,
        "before": {
            "name": before.name if before else None,
            "id": str(before.id) if before else None,
            "type": str(before.type) if isinstance(before, discord.abc.GuildChannel) else None,
        },
        "after": {
            "name": after.name if after else None,
            "id": str(after.id) if after else None,
            "type": str(after.type) if isinstance(after, discord.abc.GuildChannel) else None,
        },
        "event_time": str(formatted_time)
    }
    await log_event_to_db(guild_id, event_type, data)
