import discord
from discord.ext import commands

import logging
import tracemalloc
import asyncio
import os
from utils import send_bot


logging.basicConfig(level=logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
tracemalloc.start()

intents = discord.Intents.all()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)
send_bot(bot)
send_bot(bot)

from DataBase.db_control import (check_and_initialize_main_db, get_token_from_db, request_token)
from ActivityControl.activity_monitoring import periodic_check_for_guilds
from ChannelControl.buttons import update_buttons_on_start

from commands import create_party_search_channel, game_popularity_chart, top_games_command, language


# Словарь для хранения приглашений
invitations = {}

# Команды




async def start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()

    await update_buttons_on_start()

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
        print(f'{member.name} joined via invitation {invite_code}, invited by {inviter.name}.')
    else:
        print(f'{member.name} joined without being invited by any other member.')

    # Обновляем информацию о приглашениях
    invitations[guild.id] = invites_after



# Импорт функций и добавление к прослушиванию событий
from ChannelControl.voice_channels_control import find_party_controller
from MemberControl.role_control import game_role_reaction_add, game_role_reaction_remove

listeners = {
    'on_ready': 'start',
    'on_member_join': 'join_from_invite',
    'on_voice_state_update': 'find_party_controller',
    'on_raw_reaction_add': 'game_role_reaction_add',
    'on_raw_reaction_remove': 'game_role_reaction_remove'
}

def add_listeners():
    for event_type, handler in listeners.items():
        bot.add_listener(globals()[handler], event_type)

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