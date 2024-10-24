import json
import discord
import re
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io

from Modules.db_control import log_event_to_db, read_from_guild_settings_db, write_to_members_db, read_member_data_from_db
from utils import clean_channel_id, extract_emoji
from Modules.phrases import get_phrase


async def extract_fields(readable_data: str, event_type: str, guild) -> str:
    try:
        if isinstance(readable_data, str):
            data_dict = json.loads(readable_data.replace("'", "\""))
        else:
            return "Invalid data format: expected a string."

        if not isinstance(data_dict, dict):
            return "Decoded data is not a dictionary."

        if event_type == "new_message":
            channel = data_dict['message']['channel']
            category = channel.get('category', None)

            category_id = category if isinstance(category, str) else None
            channel_id = channel['id']
            author_id = data_dict['message']['author']['id']
            content = data_dict['message']['content'].replace("\\n", "\n")
            created_at = data_dict['message']['created_at']

            return (f"**{await get_phrase('Category', guild)}**: <#{category_id}>\n"
                    f"**{await get_phrase('Channel', guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase('Author', guild)}**: <@{author_id}>\n"
                    f"**{await get_phrase('Created At', guild)}**: {created_at}\n"
                    f"**{await get_phrase('Content', guild)}**:\n```{content}```")

        elif event_type == "edited_message":
            channel = data_dict['channel']
            channel_id = channel['id']
            author_id = data_dict['author']['id']
            author_name = data_dict['author']['name']
            content_before = data_dict['content_before'].replace("\\n", "\n")
            content_after = data_dict['content_after'].replace("\\n", "\n")
            edited_at = data_dict['edited_at']

            return (f"**{await get_phrase('Channel', guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase('Author', guild)}**: <@{author_id}> (Name: {author_name})\n"
                    f"**{await get_phrase('Edited At', guild)}**: {edited_at}\n"
                    f"**{await get_phrase('Content Before', guild)}**:\n```{content_before}```\n"
                    f"**{await get_phrase('Content After', guild)}**:\n```{content_after}```")

        elif event_type == "deleted_message":
            message = data_dict['message']
            channel_id = message['channel']['id']
            author_id = message['author']['id']
            author_name = message['author']['name']
            content = message['content'].replace("\\n", "\n")
            deleted_at = message['deleted_at']

            return (f"**{await get_phrase('Channel', guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase('Author', guild)}**: <@{author_id}> (Name: {author_name})\n"
                    f"**{await get_phrase('Deleted At', guild)}**: {deleted_at}\n"
                    f"**{await get_phrase('Content', guild)}**:\n```{content}```")

        elif event_type == "member_joined":
            member = data_dict['member']
            inviter_id = member['inviter']['id']
            invite_code = member['invite_code']
            member_name = member['name']
            member_discriminator = member['discriminator']
            joined_at = member['joined_at']

            return (f"**{await get_phrase('Member', guild)}**: {member_name}#{member_discriminator} <@{member['id']}>\n"
                    f"**{await get_phrase('Invited by', guild)}**: <@{inviter_id}>\n"
                    f"**{await get_phrase('Invite Code', guild)}**: `{invite_code}`\n"
                    f"**{await get_phrase('Joined At', guild)}**: {joined_at}\n")

        elif event_type == "member_left":
            member = data_dict['member']
            member_name = member['name']
            member_discriminator = member['discriminator']
            left_at = member['left_at']

            return (f"**{await get_phrase('Member', guild)}**: {member_name}#{member_discriminator} <@{member['id']}>\n"
                    f"**{await get_phrase('Left At', guild)}**: {left_at}\n")

        elif event_type == "member_muted":
            member = data_dict['member']
            reason = member['reason']
            duration = member['duration']
            muted_at = member['muted_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Muted At', guild)}**: {muted_at}\n"
                f"**{await get_phrase('Reason', guild)}**: {reason or await get_phrase('No reason provided', guild)}\n"
                f"**{await get_phrase('Duration', guild)}**: {duration or await get_phrase('Indefinite', guild)}\n")

        elif event_type == "member_unmuted":
            member = data_dict['member']
            reason = member['reason']
            unmuted_at = member['unmuted_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Unmuted At', guild)}**: {unmuted_at}\n"
                f"**{await get_phrase('Reason', guild)}**: {reason or await get_phrase('No reason provided', guild)}\n"
            )

        elif event_type == "member_banned":
            member = data_dict['member']
            reason = member['reason']
            banned_at = member['banned_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Banned At', guild)}**: {banned_at}\n"
                f"**{await get_phrase('Reason', guild)}**: {reason or await get_phrase('No reason provided', guild)}\n")

        elif event_type == "voice_joined":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            joined_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Joined Voice Channel', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Joined At', guild)}**: {joined_at}\n"
            )

        elif event_type == "voice_left":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            left_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Left Voice Channel', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Left At', guild)}**: {left_at}\n"
            )

        elif event_type == "voice_switched":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            switched_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Switched Voice Channels', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Switched At', guild)}**: {switched_at}\n"
            )

        elif event_type == "voice_mute":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            muted_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Muted Microphone', guild)}**\n"
                f"**{await get_phrase('Voice Channel', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Muted At', guild)}**: {muted_at}\n"
            )

        elif event_type == "voice_deaf":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            deafened_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Deafened', guild)}**\n"
                f"**{await get_phrase('Voice Channel', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Deafened At', guild)}**: {deafened_at}\n"
            )

        elif event_type == "role_created":
            role = data_dict['role']
            return (f"**{await get_phrase('Role', guild)}**: {role['name']} (ID: {role['id']})\n"
                    f"**{await get_phrase('Created At', guild)}**: {role['created_at']}\n")

        elif event_type == "role_deleted":
            role = data_dict['role']
            return (f"**{await get_phrase('Role', guild)}**: {role['name']} (ID: {role['id']})\n"
                    f"**{await get_phrase('Deleted At', guild)}**: {role['deleted_at']}\n")

        elif event_type == "role_updated":
            before_role = data_dict['before']
            after_role = data_dict['after']
            return (f"**{await get_phrase('Role Updated', guild)}**\n"
                    f"**{await get_phrase('Before', guild)}**: {before_role['name']} (ID: {before_role['id']})\n"
                    f"**{await get_phrase('After', guild)}**: {after_role['name']} (ID: {after_role['id']})\n")

        elif event_type == "channel_created":
            channel = data_dict['channel']
            return (f"**{await get_phrase('Channel', guild)}**: {channel['name']} (ID: {channel['id']})\n"
                    f"**{await get_phrase('Created At', guild)}**: {channel['created_at']}\n")

        elif event_type == "channel_deleted":
            channel = data_dict['channel']
            return (f"**{await get_phrase('Channel', guild)}**: {channel['name']} (ID: {channel['id']})\n"
                    f"**{await get_phrase('Deleted At', guild)}**: {channel['deleted_at']}\n")

        elif event_type == "channel_updated":
            before_channel = data_dict['before']
            after_channel = data_dict['after']
            return (f"**{await get_phrase('Channel Updated', guild)}**\n"
                    f"**{await get_phrase('Before', guild)}**: {before_channel['name']} (ID: {before_channel['id']})\n"
                    f"**{await get_phrase('After', guild)}**: {after_channel['name']} (ID: {after_channel['id']})\n")




        else:
            return "Event type not recognized."

    except json.JSONDecodeError:
        return "Failed to decode readable_data. Ensure it is in the correct format."
    except Exception as e:
        return f"An error occurred: {str(e)}"



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
                    # await log_channel.send(embed=embed)
                    # Not recommended to avoid spam and exceeding rate limits

    data = {
        "find_tags": "сообщение, сообщения, написал, чат",
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
            "created_at": str(formatted_time),
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
        "find_tags": "сообщение, сообщения, удалил, удалено",
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
        "find_tags": "сообщение, сообщения, изменил, отредактировала, отредактированное, отредактированные",
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
        "find_tags": "пришел, пришёл, присоединился, присоединение",
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
        "find_tags": "ушел, ушёл, ушла, ушли, покинула, покинули, ливнула, ливнули",
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
        "find_tags": "мут, мют, молчание, молчанку, молчанка",
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
        "find_tags": "размут, размьют, молчание, молчанку, молчанка",
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
        "find_tags": "бан, банан",
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
        event_type = ''

        event_description = None
        find_tags = "голосовой, голосовые, войс, "
        if before.channel is None and after.channel is not None:
            event_description = f"**{await get_phrase('Joined Voice Channel', member.guild)}**"
            event_type = "voice_joined"
            find_tags += "подключение, подключился, подключились, подключилась"
        elif before.channel is not None and after.channel is None:
            event_description = f"**{await get_phrase('Left Voice Channel', member.guild)}**"
            event_type = "voice_left"
            find_tags += "отключение, отключился, отключились, отключилась"
        elif before.channel != after.channel:
            event_description = f"**{await get_phrase('Switched Voice Channels', member.guild)}**"
            event_type = "voice_switched"
            find_tags += "смена, перешел, перешла, перешли"
        elif before.self_mute != after.self_mute:
            if after.self_mute:
                event_description = f"**{await get_phrase('Muted Microphone', member.guild)}**"
            else:
                event_description = f"**{await get_phrase('Unmuted Microphone', member.guild)}**"
            event_type = "voice_mute"
            find_tags += "микрофон, мут, мьют"
        elif before.self_deaf != after.self_deaf:
            if after.self_deaf:
                event_description = f"**{await get_phrase('Deafened', member.guild)}**"
            else:
                event_description = f"**{await get_phrase('Undeafened', member.guild)}**"
            event_type = "voice_deaf"
            find_tags += "звук, уши, наушники, выключил, включил"

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
        "find_tags": find_tags,
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


async def check_and_log_channel_changes(guild, before, after, event_type):
    changes = {}

    previous_permissions = before.overwrites
    current_permissions = after.overwrites

    if previous_permissions != current_permissions:
        changes['permissions'] = (previous_permissions, current_permissions)

    current_channel_data = {}
    for role in current_permissions:
        overwrite = current_permissions[role]
        current_channel_data[role.id] = {
            'read_messages': overwrite.read_messages,
            'send_messages': overwrite.send_messages,
            'manage_messages': overwrite.manage_messages,
            'manage_channels': overwrite.manage_channels,
            'connect': overwrite.connect,
        }

    await write_to_members_db(after, "channel_data", current_channel_data)

    return changes


async def check_and_log_role_changes(guild, before, after, event_type):
    role_id = after.id if after else before.id
    role_data = await read_member_data_from_db(role_id, "role_data")

    current_role_data = {
        "name": after.name if after else before.name,
        "permissions": str(after.permissions.value) if after else str(before.permissions.value),
        "color": str(after.color) if after else str(before.color),
        "position": after.position if after else before.position
    }

    if not role_data:
        await write_to_members_db(after, "role_data", current_role_data)
        return None

    previous_role_data = role_data["data"]
    changes = {}

    for key in current_role_data:
        if current_role_data[key] != previous_role_data.get(key):
            changes[key] = (previous_role_data.get(key), current_role_data[key])

    previous_permissions = previous_role_data.get("permissions")
    current_permissions = current_role_data.get("permissions")

    if previous_permissions != current_permissions:
        changes['permissions'] = (previous_permissions, current_permissions)

    if changes:
        await write_to_members_db(after, "role_data", current_role_data)
        return changes

    return None


async def log_channel_event(event_type, before=None, after=None, guild=None, actor=None):
    async def extract_role(line):
        match = re.match(r"\*\*(.*?)\*\*:", line)
        return match.group(1) if match else None

    def remove_duplicates(seq):
        seen = set()
        result = []
        for item in seq:
            if item not in seen and not item.startswith('_'):
                seen.add(item)
                result.append(item)
        return result

    if guild is None:
        return

    description = ""
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
                    changes_description = []

                    if before is None and after is not None:
                        description += f"{f"<@{actor.id}> ({actor.name})" if actor else ""}\n**{await get_phrase('Channel Created', guild)}**: {after.mention}"
                    elif before is not None and after is None:
                        description += f"{f"<@{actor.id}> ({actor.name})" if actor else ""}\n**{await get_phrase('Channel Deleted', guild)}**: {before.name}"
                    else:
                        changes = {}

                        if before.category != after.category:
                            previous = before.category.name if before.category else "None"
                            current = after.category.name if after.category else "None"
                            changes["category"] = (previous, current)

                        if before.name != after.name:
                            changes["name"] = (before.name, after.name)

                        if hasattr(before, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
                            changes["slowmode_delay"] = (before.slowmode_delay, after.slowmode_delay)

                        if hasattr(before, 'nsfw') and before.nsfw != after.nsfw:
                            changes["nsfw"] = (before.nsfw, after.nsfw)

                        if hasattr(before, 'bitrate') and before.bitrate != after.bitrate:
                            changes["bitrate"] = (before.bitrate, after.bitrate)

                        if hasattr(before, 'user_limit') and before.user_limit != after.user_limit:
                            changes["user_limit"] = (before.user_limit, after.user_limit)

                        if hasattr(before, 'overwrites') and before.overwrites != after.overwrites:
                            changes["permissions"] = (before.overwrites, after.overwrites)

                        if changes:
                            for key, (previous, current) in changes.items():
                                if key == "category":
                                    changes_description.append(f"**{await get_phrase('Category', guild)}**: {previous} → {current}")
                                elif key == "name":
                                    changes_description.append(f"**{await get_phrase('Name', guild)}**: {previous} → {current}")
                                elif key == "slowmode_delay":
                                    previous_value = "off" if previous == 0 else f"{previous} seconds"
                                    current_value = "off" if current == 0 else f"{current} seconds"
                                    changes_description.append(f"**{await get_phrase('Slowmode', guild)}**: {previous_value} → {current_value}")
                                elif key == "nsfw":
                                    changes_description.append(f"**{await get_phrase('NSFW', guild)}**: {'Enabled' if current else 'Disabled'}")
                                elif key == "bitrate":
                                    changes_description.append(f"**{await get_phrase('Bitrate', guild)}**: {previous} kbps → {current} kbps")
                                elif key == "user_limit":
                                    previous_value = "No limit" if previous == 0 else str(previous)
                                    current_value = "No limit" if current == 0 else str(current)
                                    changes_description.append(f"**{await get_phrase('User Limit', guild)}**: {previous_value} → {current_value}")
                                elif key == "permissions":
                                    previous_permissions = await format_permissions(previous)
                                    current_permissions = await format_permissions(current)

                                    differences = []
                                    for role, overwrite in current.items():
                                        if role in previous:
                                            previous_overwrite = previous[role]
                                            for perm in dir(overwrite):
                                                if not perm.startswith('_') and perm in dir(previous_overwrite):
                                                    previous_value = getattr(previous_overwrite, perm)
                                                    current_value = getattr(overwrite, perm)
                                                    if previous_value != current_value:
                                                        perm_name = await get_phrase(perm, guild)
                                                        differences.append(f"{role.name} - {perm_name}: {'✅' if previous_value else '❌'} → {'✅' if current_value else '❌'}")
                                        else:
                                            for perm in dir(overwrite):
                                                if not perm.startswith('_'):
                                                    value = getattr(overwrite, perm)
                                                    if value is not None:
                                                        perm_name = await get_phrase(perm, guild)
                                                        differences.append(f"{role.name} - {perm_name}: {'❌'} → {'✅' if value else '❌'}")

                                    if differences:
                                        changes_description.append(f"**{await get_phrase('Permissions', guild)}**:" + "\n".join(differences))
                                    else:
                                        changes_description.append(f"**{await get_phrase('Permissions', guild)}**:"
                                                                   f" {await get_phrase('no changes found', guild)}")

                            if changes_description:
                                description += f"{f"<@{actor.id}> ({actor.name})" if actor else ""}\n**{await get_phrase('Changes', guild)}** {after.mention}:\n" + "\n".join(changes_description)

                    description_lines = description.splitlines()
                    filtered_lines = []
                    for line in description_lines:
                        if line.count('✅') == 2 or line.count('❌') == 2:
                            continue
                        filtered_lines.append(line)
                    description = "\n".join(filtered_lines)

                    embed = discord.Embed(color=discord.Color.from_str("#6B8E23"))
                    embed.description = description
                    if description:
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
        "permissions": description,
        "event_time": str(formatted_time),
        "actor_id": str(actor.id) if actor else None
    }
    await log_event_to_db(guild_id, event_type, data)


async def format_permissions(overwrites):
    if not overwrites:
        return "Нет доступных данных"

    permissions_list = []
    for target, overwrite in overwrites.items():
        perm_values = {
            perm: value for perm, value in overwrite if value is not None
        }

        permissions_description = ",\n".join(
            [f"{perm}: {'✅' if value else '❌'}" for perm, value in perm_values.items()]
        )
        permissions_list.append(f"**{target.name}**: {permissions_description}")

    return "\n".join(permissions_list)




async def log_role_event(event_type, before=None, after=None, guild=None, actor=None):
    if guild is None:
        return

    description = f"<@{actor.id}> ({actor.name})\n"
    file = None
    embed = None
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
                    if before is None and after is not None:
                        description += f"**{await get_phrase('Role created', guild)}**:\n{after.mention}"
                        embed = discord.Embed(color=discord.Color.green())
                        embed.description = description
                        await log_channel.send(embed=embed)

                    elif before is not None and after is None:
                        description += f"**{await get_phrase('Role deleted', guild)}**:\n{before.name}"
                        embed = discord.Embed(color=discord.Color.red())
                        embed.description = description
                        await log_channel.send(embed=embed)

                    else:
                        changes = await check_and_log_role_changes(guild, before, after, event_type)

                        if changes:
                            changes_description = []
                            for key, (previous, current) in changes.items():
                                if key == "permissions":
                                    if isinstance(previous, str) and isinstance(current, str):
                                        previous_permissions = await format_role_permissions(before.permissions)
                                        current_permissions = await format_role_permissions(after.permissions)
                                        differences = await format_role_permissions_diff(before.permissions, after.permissions)
                                        if differences:
                                            changes_description.append(f"**{await get_phrase('Permissions', guild)}**:\n" + differences)
                                        else:
                                            changes_description.append(f"**{await get_phrase('Permissions', guild)}**: {await get_phrase('no changes found', guild)}")
                                elif key == "position":
                                    # Only log position changes to the database, do not send a message
                                    continue
                                elif key == "color":
                                    file = await generate_color_change_image(previous, current)
                                    embed = discord.Embed(color=discord.Color.from_str(current))
                                    changes_description.append(
                                        f"**{await get_phrase('Color', guild)}**: {previous} → {current}")
                                else:
                                    changes_description.append(f"**{await get_phrase(key.capitalize(), guild)}**: {previous} → {current}")

                            if changes_description:
                                if embed is None:
                                    embed = discord.Embed(color=discord.Color.from_str("#7CFC00"))
                                description += f"\n**{await get_phrase('Changes', guild)}** {after.mention}:\n" + "\n".join(
                                    changes_description)
                                embed.description = description
                                if file is not None:
                                    image_bytes = file.fp
                                    embed.set_image(url="attachment://color_change.png")
                                    await log_channel.send(embed=embed, file=discord.File(fp=image_bytes, filename="color_change.png"))
                                else:
                                    await log_channel.send(embed=embed)

    data = {
        "event_type": event_type,
        "before": {
            "name": before.name if before else None,
            "id": str(before.id) if before else None,
        },
        "after": {
            "name": after.name if after else None,
            "id": str(after.id) if after else None,
        },
        "permissions": description,
        "event_time": str(formatted_time),
        "actor_id": str(actor.id) if actor else None
    }
    await log_event_to_db(guild_id, event_type, data)


async def format_role_permissions(overwrites):
    if not overwrites:
        return "Нет доступных данных"

    permissions_list = []
    for perm in PERMISSIONS:
        value = getattr(overwrites, perm, None)
        if isinstance(value, bool):
            permissions_list.append(f"{perm}: {'✅' if value else '❌'}")

    return "\n".join(permissions_list)


async def format_role_permissions_diff(previous_permissions, current_permissions):
    differences = []
    for perm in PERMISSIONS:
        prev_value = getattr(previous_permissions, perm, None)
        curr_value = getattr(current_permissions, perm, None)
        if isinstance(prev_value, bool) and isinstance(curr_value, bool) and prev_value != curr_value:
            differences.append(f"{perm}: {'✅' if prev_value else '❌'} → {'✅' if curr_value else '❌'}")
    return "\n".join(differences)


async def generate_color_change_image(old_color, new_color):
    image = Image.new("RGBA", (400, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    for x in range(400):
        r = 112 + int((47 / 400) * x)
        g = 128 + int((79 / 400) * x)
        b = 144 + int((79 / 400) * x)
        draw.line([(x, 0), (x, 50)], fill=(r, g, b))

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()

    old_text_bbox = draw.textbbox((0, 0), "OLD", font=font)
    old_text_width, old_text_height = old_text_bbox[2] - old_text_bbox[0], old_text_bbox[3] - old_text_bbox[1]
    draw.text(((200 - old_text_width) / 2, (50 - old_text_height) / 2), "OLD", fill="white", font=font)

    new_text_bbox = draw.textbbox((0, 0), "NEW", font=font)
    new_text_width, new_text_height = new_text_bbox[2] - new_text_bbox[0], new_text_bbox[3] - new_text_bbox[1]
    draw.text((200 + (200 - new_text_width) / 2, (50 - new_text_height) / 2), "NEW", fill="black", font=font)

    if isinstance(old_color, str):
        old_color = ImageColor.getrgb(old_color)
    if isinstance(new_color, str):
        new_color = ImageColor.getrgb(new_color)

    draw.rectangle([0, 50, 100, 200], fill=old_color)

    for x in range(100, 300):
        ratio = (x - 100) / 200
        r = int(old_color[0] * (1 - ratio) + new_color[0] * ratio)
        g = int(old_color[1] * (1 - ratio) + new_color[1] * ratio)
        b = int(old_color[2] * (1 - ratio) + new_color[2] * ratio)
        draw.line([(x, 50), (x, 200)], fill=(r, g, b))

    draw.rectangle([300, 50, 400, 200], fill=new_color)

    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    file = discord.File(fp=image_bytes, filename=f"{old_color}-{new_color}.png")
    return file



PERMISSIONS = (
    "DEFAULT_VALUE",
    "VALID_FLAGS",
    "add_reactions",
    "administrator",
    "advanced",
    "all",
    "all_channel",
    "attach_files",
    "ban_members",
    "change_nickname",
    "connect",
    "create_events",
    "create_expressions",
    "create_instant_invite",
    "create_polls",
    "create_private_threads",
    "create_public_threads",
    "deafen_members",
    "elevated",
    "embed_links",
    "events",
    "external_emojis",
    "external_stickers",
    "general",
    "handle_overwrite",
    "is_strict_subset",
    "is_strict_superset",
    "is_subset",
    "is_superset",
    "kick_members",
    "manage_channels",
    "manage_emojis",
    "manage_emojis_and_stickers",
    "manage_events",
    "manage_expressions",
    "manage_guild",
    "manage_messages",
    "manage_nicknames",
    "manage_permissions",
    "manage_roles",
    "manage_threads",
    "manage_webhooks",
    "membership",
    "mention_everyone",
    "moderate_members",
    "move_members",
    "mute_members",
    "none",
    "priority_speaker",
    "read_message_history",
    "read_messages",
    "request_to_speak",
    "send_messages",
    "send_messages_in_threads",
    "send_polls",
    "send_tts_messages",
    "send_voice_messages",
    "speak",
    "stage",
    "stage_moderator",
    "stream",
    "text",
    "update",
    "use_application_commands",
    "use_embedded_activities",
    "use_external_apps",
    "use_external_emojis",
    "use_external_sounds",
    "use_external_stickers",
    "use_soundboard",
    "use_voice_activation",
    "value",
    "view_audit_log",
    "view_channel",
    "view_creator_monetization_analytics",
    "view_guild_insights",
    "voice",
)
