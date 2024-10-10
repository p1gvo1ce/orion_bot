import discord
from discord.ext import commands
from discord import app_commands
import logging
import tracemalloc
import asyncio
import os

from DataBase.db_control import check_and_initialize_main_db, get_token_from_db, request_token, get_top_games
from ActivityControl.activity_monitoring import periodic_check_for_guilds
from Analytics.analytics import plot_top_games, top_games_create_embed

logging.basicConfig(level=logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
tracemalloc.start()

joined = []
intents = discord.Intents.all()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)


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


async def start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()
    await periodic_check_for_guilds(bot)


def add_listeners():
    bot.add_listener(start, 'on_ready')


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