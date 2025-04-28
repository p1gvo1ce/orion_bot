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
from Modules.logger import (log_joined_member, log_channel_event, log_voice_state_update, log_member_banned,
                            log_member_muted, log_member_left, log_member_unmuted, log_role_event)

from utils import get_bot
from Modules.greetings import greetings

bot = get_bot()

invitations = {}


GREETING_CHANNEL_ID = 930430671086845953

async def bot_start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()
    await check_and_remove_nonexistent_channels()
    for guild in bot.guilds:
        invitations[guild.id] = await guild.invites()
    await periodic_check_for_guilds(bot)

async def start_copy_logs_to_analytics():
    await copy_logs_to_analytics(bot.guilds)



# --- Persistent Greeting View ---
class GreetingView(discord.ui.View):
    def __init__(self, member: discord.Member):
        # persistent=True для вечных кнопок
        super().__init__(timeout=None, persistent=True)
        self.member = member
        btn = discord.ui.Button(
            label='Помашите и поздоровайтесь',
            custom_id=f'greet_{member.id}',
            style=discord.ButtonStyle.primary
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
            if greeter.id == uid:
                desc = f'{greeter.mention} приветствует всех!'
            else:
                desc = f'{greeter.mention} приветствует {target.mention}'
            embed = discord.Embed(title='Новый привет!', description=desc, color=0x66CDAA)

            # выбираем случайный GIF из локальной папки
            gifs_dir = 'gifs/greetings'
            try:
                files = [f for f in os.listdir(gifs_dir) if f.lower().endswith('.gif')]
                filename = random.choice(files)
                file_path = os.path.join(gifs_dir, filename)
                discord_file = discord.File(file_path, filename=filename)
                embed.set_image(url=f"attachment://{filename}")
                await interaction.response.send_message(
                    embed=embed,
                    file=discord_file,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                sent = await interaction.original_response()
            except Exception:
                await interaction.response.send_message(
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                sent = await interaction.original_response()

            # удаляем именно это сообщение через 2 минуты
            async def delete_later(msg):
                await asyncio.sleep(120)
                try:
                    await msg.delete()
                except:
                    pass
            asyncio.create_task(delete_later(sent))
        else:
            try:
                await interaction.message.delete()
            except:
                pass

# --- Bot startup and persistent view registration ---
@bot.event
async def on_ready_check_greetings_buttons():
    print(f'Logged in as {bot.user}')
    # Синхронизируем команды
    await bot.tree.sync()
    # Чистим устаревшие каналы
    await check_and_remove_nonexistent_channels()

    # Сохраняем текущие инвайты
    for guild in bot.guilds:
        invitations[guild.id] = await guild.invites()

    # Запускаем периодические задачи
    asyncio.create_task(periodic_check_for_guilds(bot))
    asyncio.create_task(copy_logs_to_analytics(bot.guilds))

    # Регистрируем persistent views для уже отправленных приветствий
    channel = bot.get_channel(GREETING_CHANNEL_ID)
    if channel:
        async for msg in channel.history(limit=200):
            if msg.author.id == bot.user.id and msg.components:
                # находим кнопку с custom_id "greet_<id>"
                for row in msg.components:
                    for comp in row.children:
                        cid = getattr(comp, 'custom_id', '')
                        if cid.startswith('greet_'):
                            _, uid_str = cid.split('_', 1)
                            member = msg.guild.get_member(int(uid_str))
                            if member:
                                view = GreetingView(member)
                                # регистрируем View для конкретного сообщения
                                bot.add_view(view, message_id=msg.id)
                            break


async def join_from_invite(member):
    # Send greeting prompt in the specific channel
    channel = member.guild.get_channel(861309266617696327)
    if not channel or not channel.permissions_for(member.guild.me).send_messages:
        return

    view = GreetingView(member)
    # Send a welcome message tagging the new member
    await channel.send(f'Встречайте {member.mention}! Не стесняйтесь поздороваться 👋', view=view)


async def greetings_delete_greetings(message):
    # Отслеживаем конкретный канал
    if message.channel.id == 930430671086845953:
        # Только сообщения бота с приветствием
        if message.author.id == bot.user.id and "Встречайте" in message.content:
            # Ищем первое упоминание участника
            match = re.search(r"<@!?(\d+)>", message.content)
            if match:
                uid = int(match.group(1))
                # Если участник уже не в гильдии — удаляем сообщение
                if not message.guild.get_member(uid):
                    await message.delete()
    # Всегда продолжаем обработку команд
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