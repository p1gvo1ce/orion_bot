import discord
import asyncio
import random
from datetime import datetime
from discord import Permissions

from Modules.buttons import update_buttons_on_start
from Modules.activity_monitoring import periodic_check_for_guilds
from Modules.db_control import read_from_guild_settings_db, copy_logs_to_analytics
from Modules.voice_channels_control import check_and_remove_nonexistent_channels
from Modules.logger import (log_joined_member, log_channel_event, log_voice_state_update, log_member_banned,
                            log_member_muted, log_member_left, log_member_unmuted, log_role_event)

from utils import get_bot
from Modules.greetings import greetengs

bot = get_bot()

invitations = {}

async def bot_start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()
    await check_and_remove_nonexistent_channels()
    for guild in bot.guilds:
        invitations[guild.id] = await guild.invites()
    await periodic_check_for_guilds(bot)

async def start_copy_logs_to_analytics():
    await copy_logs_to_analytics(bot.guilds)




class GreetingView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member
        # Button with custom_id embedding the new member's ID
        self.add_item(discord.ui.Button(
            label='Помашите и поздоровайтесь',
            custom_id=f'greet_{member.id}',
            style=discord.ButtonStyle.primary
        ))

    @discord.ui.button(label='Помашите и поздоровайтесь', style=discord.ButtonStyle.primary)
    async def greet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Extract user ID from button custom_id
        _, uid = button.custom_id.split('_')
        uid = int(uid)
        guild = interaction.guild
        target = guild.get_member(uid)

        # If user still in guild, send embed greeting
        if target:
            greeter = interaction.user
            embed = discord.Embed(
                title='Новый привет!',
                description=f'{greeter.mention} приветствует {target.mention}',
                color=discord.Color.blue()
            )
            embed.set_image(url=random.choice(greetings))

            greeting_msg = await interaction.response.send_message(embed=embed, mention_author=False)

            # Schedule deletion after 2 minutes
            async def delete_later(msg: discord.Message):
                await asyncio.sleep(120)
                try:
                    await msg.delete()
                except Exception:
                    pass

            # Grab the sent message object from the response
            if isinstance(greeting_msg, discord.Message):
                msg_obj = greeting_msg
            else:
                # fetch last message in channel by bot
                history = await interaction.channel.history(limit=1).flatten()
                msg_obj = history[0]

            asyncio.create_task(delete_later(msg_obj))
        else:
            # Member left, remove the button message
            try:
                await interaction.message.delete()
            except Exception:
                pass


async def join_from_invite(member):
    # Send greeting prompt in a default channel (adjust as needed)
    channel = member.guild.get_channel(861309266617696327 )
    if not channel:
        return

    view = GreetingView(member)
    # Send a welcome-type message tagging the new member
    await channel.send(f'Встречайте {member.mention}! Не стесняйтесь поздороваться 👋', view=view)


async def greetings_delete_greetings(message):
    # Monitor specific channel for stale greeting buttons
    if message.channel.id == 930430671086845953:
        # Look back at the last 10 messages
        async for msg in message.channel.history(limit=10):
            if msg.author == bot.user and msg.components:
                for row in msg.components:
                    for comp in row.children:
                        custom = getattr(comp, 'custom_id', '')
                        if custom.startswith('greet_'):
                            _, uid = custom.split('_')
                            uid = int(uid)
                            # If member no longer on server, delete the prompt
                            if not msg.guild.get_member(uid):
                                await msg.delete()
    # Ensure commands still process
    await bot.process_commands(message)

async def get_actor(guild):
    async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_update, limit=1):
        return entry.user
    return None

async def on_guild_role_create(role):
    await log_role_event("role_created", after=role, guild=role.guild, actor=await get_actor(role.guild))

async def on_guild_role_update(before, after):
    await log_role_event("role_updated", before=before, after=after, guild=before.guild, actor=await get_actor(before.guild))

async def on_guild_role_delete(role):
    await log_role_event("role_deleted", before=role, guild=role.guild, actor=await get_actor(role.guild))

async def on_guild_channel_create(channel):
    await log_channel_event("channel_created", after=channel, guild=channel.guild, actor=await get_actor(channel.guild))

async def on_guild_channel_update(before, after):
    await log_channel_event("channel_updated", before=before, after=after, guild=before.guild, actor=await get_actor(before.guild))

async def on_guild_channel_delete(channel):
    await log_channel_event("channel_deleted", before=channel, guild=channel.guild, actor=await get_actor(channel.guild))

async def on_voice_state_update(member, before, after):
    await log_voice_state_update(member, before, after)

async def on_member_ban(guild, user):
    member = guild.get_member(user.id)
    if member:
        reason = None
        await log_member_banned(member, reason)

async def on_member_update(before, after):
    if hasattr(before, 'communication_disabled_until') and hasattr(after, 'communication_disabled_until'):
        if before.communication_disabled_until is None and after.communication_disabled_until is not None:
            reason = "Muted by admin"
            duration = (after.communication_disabled_until - datetime.utcnow()).total_seconds()
            await log_member_muted(after, reason=reason, duration=duration)

        elif before.communication_disabled_until is not None and after.communication_disabled_until is None:
            reason = "Unmuted by admin"
            await log_member_unmuted(after, reason=reason)



async def on_member_remove(member):
    await log_member_left(member)