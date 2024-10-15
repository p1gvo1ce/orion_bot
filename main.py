import logging
import tracemalloc
import asyncio
import os

from utils import get_bot
bot = get_bot()
from Modules.db_control import (check_and_initialize_main_db, get_token_from_db, request_token)
from Modules.buttons import update_buttons_on_start
from Modules.commands import (create_party_search_channel, game_popularity_chart, top_games_command, language,
                              create_top_games_roles)
from Modules.voice_channels_control import find_party_controller
from Modules.role_control import game_role_reaction_add, game_role_reaction_remove
from Modules.events import start, join_from_invite, greetings_delete_greetings


logging.basicConfig(level=logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
tracemalloc.start()

listeners = {
    'on_ready': 'start',
    'on_member_join': 'join_from_invite',
    'on_voice_state_update': 'find_party_controller',
    'on_raw_reaction_add': 'game_role_reaction_add',
    'on_raw_reaction_remove': 'game_role_reaction_remove',
    'on_message': 'greetings_delete_greetings'
}
for event_type, handler in listeners.items():
    bot.add_listener(globals()[handler], event_type)

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

    asyncio.run(run_bot(token, conn))

if __name__ == "__main__":
    main()