import discord
from discord.ext import commands
import tracemalloc
import asyncio
import os

from DataBase.db_control import check_and_initialize_db, get_token_from_db, request_token
from ActivityControl.activity_monitoring import periodic_check_for_guilds

tracemalloc.start()

joined = []
intents = discord.Intents.all()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)



async def start():
    print(f'Logged in as {bot.user.name}')
    await periodic_check_for_guilds(bot)


def add_listeners():
    bot.add_listener(start, 'on_ready')


add_listeners()

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
    conn = check_and_initialize_db()
    token = get_token_from_db(conn)

    if not token:
        print("Токен не найден.")
        token = request_token(conn)

    asyncio.run(run_bot(token, conn))  # Запуск бота

if __name__ == "__main__":
    main()