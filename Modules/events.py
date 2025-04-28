import discord
import asyncio
import random
import os
import re
from datetime import datetime
from discord import Permissions

from Modules.buttons import update_buttons_on_start
from Modules.activity_monitoring import periodic_check_for_guilds
from Modules.db_control import read_from_guild_settings_db, copy_logs_to_analytics
from Modules.voice_channels_control import check_and_remove_nonexistent_channels
from Modules.logger import (
    log_joined_member, log_channel_event, log_voice_state_update, log_member_banned,
    log_member_muted, log_member_left, log_member_unmuted, log_role_event
)

from utils import get_bot
from Modules.greetings import greetings  # список URL GIF или можно оставить локальную папку

bot = get_bot()

invitations = {}

async def bot_start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()
    await check_and_remove_nonexistent_channels()
    for guild in bot.guilds:
        invitations[guild.id] = await guild.invites()
    await periodic_check_for_guilds(bot)
    # Можно также запускать копирование логов
    asyncio.create_task(copy_logs_to_analytics(bot.guilds))

async def start_copy_logs_to_analytics():
    await copy_logs_to_analytics(bot.guilds)


class GreetingView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member
        btn = discord.ui.Button(
            label='👋 Помашите и поздоровайтесь',
            custom_id=f'greet_{member.id}',
            style=discord.ButtonStyle.success
        )
        btn.callback = self.greet_callback
        self.add_item(btn)

    async def greet_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data.get('custom_id', '')
        if not custom_id.startswith('greet_'):
            return
        _, uid_str = custom_id.split('_', 1)
        uid = int(uid_str)

        guild = interaction.guild
        target = guild.get_member(uid)

        if target:
            greeter = interaction.user
            # проверка на self-greet
            if greeter.id == uid:
                description = f'{greeter.mention} приветствует всех!'
            else:
                description = f'{greeter.mention} приветствует {target.mention}'

            embed = discord.Embed(
                title='Новый привет!',
                description=description,
                color=0x66CDAA
            )

            # выбор GIF: можно из локальной папки
            gifs_dir = 'gifs/greetings'
            try:
                files = [f for f in os.listdir(gifs_dir) if f.lower().endswith('.gif')]
                filename = random.choice(files)
                file_path = os.path.join(gifs_dir, filename)
                discord_file = discord.File(file_path, filename=filename)
                embed.set_image(url=f'attachment://{filename}')
                await interaction.response.send_message(
                    embed=embed,
                    file=discord_file,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                sent_msg = await interaction.original_response()
            except Exception:
                await interaction.response.send_message(
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                sent_msg = await interaction.original_response()

            async def delete_later(msg):
                await asyncio.sleep(120)
                try:
                    await msg.delete()
                except Exception:
                    pass

            asyncio.create_task(delete_later(sent_msg))
        else:
            try:
                await interaction.message.delete()
            except Exception:
                pass


async def join_from_invite(member: discord.Member):
    channel = member.guild.get_channel(861309266617696327)  # канал для приветствий
    if not channel or not channel.permissions_for(member.guild.me).send_messages:
        return

    view = GreetingView(member)
    await channel.send(f'Встречайте {member.mention}! Не стесняйтесь поздороваться 👋', view=view)


async def greetings_delete_greetings(message):
    # Monitor specific channel for stale greeting buttons
    if message.channel.id == 930430671086845953:
        if message.author == bot.user and "Встречайте" in message.content:
            match = re.search(r'<@!?(\d+)>', message.content)
            if match:
                uid = int(match.group(1))
                if not message.guild.get_member(uid):
                    await message.delete()
    await bot.process_commands(message)


async def get_actor(guild):
    async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_update, limit=1):
        return entry.user
    return None

# Регистрируем события
@bot.event
async def on_ready():
    await bot_start()

@bot.event
async def on_member_join(member):
    # await join_from_invite(member)
    pass

@bot.event
async def on_message(message):
    await greetings_delete_greetings(message)

@bot.event
async def on_guild_role_create(role):
    await log_role_event("role_created", after=role, guild=role.guild, actor=await get_actor(role.guild))

@bot.event
async def on_guild_role_update(before, after):
    await log_role_event("role_updated", before=before, after=after, guild=before.guild, actor=await get_actor(before.guild))

@bot.event
async def on_guild_role_delete(role):
    await log_role_event("role_deleted", before=role, guild=role.guild, actor=await get_actor(role.guild))

@bot.event
async def on_guild_channel_create(channel):
    await log_channel_event("channel_created", after=channel, guild=channel.guild, actor=await get_actor(channel.guild))

@bot.event
async def on_guild_channel_update(before, after):
    await log_channel_event("channel_updated", before=before, after=after, guild=before.guild, actor=await get_actor(before.guild))

@bot.event
async def on_guild_channel_delete(channel):
    await log_channel_event("channel_deleted", before=channel, guild=channel.guild, actor=await get_actor(channel.guild))

@bot.event
async def on_voice_state_update(member, before, after):
    await log_voice_state_update(member, before, after)

@bot.event
async def on_member_ban(guild, user):
    member = guild.get_member(user.id)
    if member:
        await log_member_banned(member, None)

@bot.event
async def on_member_update(before, after):
    if hasattr(before, 'communication_disabled_until') and hasattr(after, 'communication_disabled_until'):
        if before.communication_disabled_until is None and after.communication_disabled_until is not None:
            duration = (after.communication_disabled_until - datetime.utcnow()).total_seconds()
            await log_member_muted(after, "Muted by admin", duration)
        elif before.communication_disabled_until is not None and after.communication_disabled_until is None:
            await log_member_unmuted(after, "Unmuted by admin")

@bot.event
async def on_member_remove(member):
    await log_member_left(member)
