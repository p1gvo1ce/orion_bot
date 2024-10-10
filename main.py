import discord
from discord.ext import commands
from discord import app_commands
import logging
import tracemalloc
import asyncio
import os

from DataBase.db_control import (check_and_initialize_main_db, get_token_from_db, request_token, get_top_games,
                                 write_to_guild_settings_db)
from ActivityControl.activity_monitoring import periodic_check_for_guilds
from Analytics.analytics import plot_top_games, top_games_create_embed, popularity_games_create_embed
from utils import send_bot

logging.basicConfig(level=logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
tracemalloc.start()

intents = discord.Intents.all()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)
send_bot(bot)
# Словарь для хранения приглашений
invitations = {}

# Получение анализа самых популярных игр на сервере
@bot.tree.command(name="top_games", description="Get top games for the last N days.")
@app_commands.describe(days="Number of days to analyze", top="Number of top games", granularity="Granularity (day, week, month)")

async def top_games_command(interaction: discord.Interaction, days: int, top: int, granularity: str):
    guild_id = interaction.guild_id
    guild_name = interaction.guild.name
    top_games = get_top_games(guild_id, days, granularity)
    top_games = top_games[:top]

    graph_buf = plot_top_games(guild_id, guild_name, top_games, days, granularity)

    embed = top_games_create_embed(top_games, days, granularity)

    file = discord.File(fp=graph_buf, filename="top_games.png")
    embed.set_image(url="attachment://top_games.png")
    await interaction.response.send_message(embed=embed, file=file)

# Получение графика популярности игры на сервере
@bot.tree.command(name="game_popularity_chart", description="Get game popularity chart for the last N days.")
@app_commands.describe(days="Number of days to analyze", granularity="Granularity (day, week, month)", game="Name of the game")

async def game_popularity_chart(interaction: discord.Interaction, days: int, granularity: str, game: str):
    guild_id = interaction.guild_id
    guild_name = interaction.guild.name

    graph_buf = plot_top_games(guild_id, guild_name, [], days, granularity, game)

    embed = popularity_games_create_embed(game, days, granularity)

    file = discord.File(fp=graph_buf, filename=f"{game}_popularity.png")
    embed.set_image(url=f"attachment://{game}_popularity.png")
    await interaction.response.send_message(embed=embed, file=file)

async def start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()
    for guild in bot.guilds:
        invitations[guild.id] = await guild.invites()
    await periodic_check_for_guilds(bot)

async def join_from_invite(member):
    guild = member.guild
    invites_before = invitations[guild.id]
    invites_after = await guild.invites()

    # Сравниваем приглашения, чтобы найти, по какому пригласили участника
    for invite in invites_before:
        for after in invites_after:
            if invite.code == after.code:
                # Если количество использований изменилось
                if invite.uses < after.uses:
                    inviter = invite.inviter
                    invite_code = invite.code
                    break
    if inviter:
        print(f'Member {member.name} joined via invitation {invite_code}, invited by {inviter.name}.')
    else:
        print(f'Member {member.name} joined without being invited by any other member.')

    # Обновляем информацию о приглашениях
    invitations[guild.id] = invites_after

# Создание каналов для автоматического поиска компании
@bot.tree.command(name="create_party_search_channel", description="[admin] create channels for automatic party search.")
@app_commands.describe()
@commands.has_permissions(administrator=True)
async def create_party_search_channel(interaction: discord.Interaction):
    guild = interaction.guild  # Получаем объект сервера (гильдии)

    # Создаем текстовый канал для поиска группы
    text_channel = await guild.create_text_channel('party-search-text')

    # Создаем голосовой канал для поиска группы
    voice_channel = await guild.create_voice_channel('party-search-voice')

    # ID созданных каналов и ID сервера
    text_channel_id = text_channel.id
    voice_channel_id = voice_channel.id
    guild_id = guild.id

    # Записываем информацию в базу данных
    write_to_guild_settings_db(guild_id, "party_find_text_channel_id", f"id{text_channel_id}")
    write_to_guild_settings_db(guild_id, "party_find_voice_channel_id", f"id{voice_channel_id}")

    # Отправляем сообщение о создании каналов
    await interaction.response.send_message(f"Text and voice channels for party search created:\n"
                                            f"Text Channel: {text_channel.mention}\n"
                                            f"Voice Channel: {voice_channel.mention}")


from ChannelControl.voice_channels_control import find_party_controller
from MemberControl.role_control import game_role_reaction_add, game_role_reaction_remove
def add_listeners():
    bot.add_listener(start, 'on_ready')
    bot.add_listener(join_from_invite, 'on_member_join')
    bot.add_listener(find_party_controller, 'on_voice_state_update')

    bot.add_listener(game_role_reaction_add, 'on_raw_reaction_add')
    bot.add_listener(game_role_reaction_remove, 'on_raw_reaction_remove')


add_listeners()

async def register_commands(bot):
    await bot.tree.sync()

async def run_bot(token, conn):
    retry_count = 0
    while retry_count < 3:
        try:
            await bot.start(token)
        except Exception as e:
            print(f"Бот остановлен из-за ошибки: {e}")
            if str(e) == "Improper token has been passed.":
                print(1)
                token = request_token(conn)
            else:
                os.system("python bot.py")

            retry_count += 1
            if retry_count >= 2:
                os.system("python bot.py")

def main():
    conn = check_and_initialize_main_db()
    token = get_token_from_db(conn)

    if not token:
        print("Токен не найден.")
        token = request_token(conn)

    asyncio.run(run_bot(token, conn))  # Запуск бота

if __name__ == "__main__":
    main()