import discord
import asyncio
from datetime import datetime

from Modules.buttons import update_buttons_on_start
from Modules.activity_monitoring import periodic_check_for_guilds
from Modules.db_control import read_from_guild_settings_db, copy_logs_to_analytics
from Modules.voice_channels_control import check_and_remove_nonexistent_channels
from Modules.logger import (log_joined_member, log_role_channel_event, log_voice_state_update, log_member_banned,
                            log_member_muted, log_member_left, log_member_unmuted)

from utils import get_bot

bot = get_bot()

invitations = {}

async def bot_start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()

    await update_buttons_on_start()
    await check_and_remove_nonexistent_channels()
    for guild in bot.guilds:
        invitations[guild.id] = await guild.invites()
    await periodic_check_for_guilds(bot)

async def start_copy_logs_to_analytics():
    await copy_logs_to_analytics(bot.guilds)

async def join_from_invite(member):
    inviter, invite_code = '', ''
    guild = member.guild
    invites_before = invitations[guild.id]
    invites_after = await guild.invites()

    for invite in invites_before:
        for after in invites_after:
            if invite.code == after.code:
                if invite.uses < after.uses:
                    inviter = invite.inviter
                    invite_code = invite.code
                    break


    await log_joined_member(member, inviter.id, invite_code)
    invitations[guild.id] = invites_after

async def greetings_delete_greetings(message):
    if message.reference:
        guild_settings = await read_from_guild_settings_db(message.guild.id, 'removing_greetings')
        if guild_settings and guild_settings[0] == 'on':
            delay = int((await read_from_guild_settings_db(message.guild.id, 'removing_greetings_delay'))[0])
            original_message = await message.channel.fetch_message(message.reference.message_id)
            if original_message.type == discord.MessageType.new_member and original_message.author in message.guild.members:
                await asyncio.sleep(delay)
                await message.delete()
            elif original_message.type == discord.MessageType.new_member and original_message.author not in message.guild.members:
                await message.delete()
                await original_message.delete()

async def on_guild_role_create(role):
    await log_role_channel_event("role_created", after=role, guild=role.guild)

async def on_guild_role_update(before, after):
    await log_role_channel_event("role_updated", before=before, after=after, guild=before.guild)

async def on_guild_role_delete(role):
    await log_role_channel_event("role_deleted", before=role, guild=role.guild)

async def on_guild_channel_create(channel):
    await log_role_channel_event("channel_created", after=channel, guild=channel.guild)

async def on_guild_channel_update(before, after):
    await log_role_channel_event("channel_updated", before=before, after=after, guild=before.guild)

async def on_guild_channel_delete(channel):
    await log_role_channel_event("channel_deleted", before=channel, guild=channel.guild)

async def on_voice_state_update(member, before, after):
    await log_voice_state_update(member, before, after)

async def on_member_ban(guild, user):
    member = guild.get_member(user.id)
    if member:
        reason = None
        await log_member_banned(member, reason)

async def on_member_update(before, after):
    if before.communication_disabled_until is None and after.communication_disabled_until is not None:
        reason = "Muted by admin"
        duration = (after.communication_disabled_until - datetime.utcnow()).total_seconds()
        await log_member_muted(after, reason=reason, duration=duration)

    elif before.communication_disabled_until is not None and after.communication_disabled_until is None:
        reason = "Unmuted by admin"
        await log_member_unmuted(after, reason=reason)


async def on_member_remove(member):
    await log_member_left(member)