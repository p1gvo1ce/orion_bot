import tracemalloc
import asyncio
import os
import aiohttp

from utils import get_bot
bot = get_bot()

from Modules.db_control import (check_and_initialize_main_db, get_token_from_db, request_token)
from Modules.buttons import update_buttons_on_start
from Modules.commands import (create_party_search_channel, game_popularity_chart, top_games_command, language,
                              create_top_games_roles, set_voice_name, dont_update_roles, set_utc_time, logging_system,
                              get_logs)
from Modules.voice_channels_control import find_party_controller, voice_name_moderation, channel_create_name_moderation
from Modules.role_control import game_role_reaction_add, game_role_reaction_remove
from Modules.events import (bot_start, join_from_invite, greetings_delete_greetings, start_copy_logs_to_analytics,
                            on_guild_role_create, on_guild_role_update, on_guild_role_delete, on_guild_channel_create,
                            on_guild_channel_update, on_guild_channel_delete, on_voice_state_update, on_member_ban,
                            on_member_update)
from Modules.logger import log_new_message, log_edited_message, log_deleted_message
from Modules.ublyudoshnaya import bolnoy_ublyudok

from Modules.kostili import ensure_min_voice_channels

GITHUB_API_URL = "https://api.github.com/repos/p1gvo1ce/orion_bot/commits/master"

tracemalloc.start()

listeners = {
    'on_ready': ['bot_start', 'start_copy_logs_to_analytics', 'update_buttons_on_start'],
    'on_member_join': ['join_from_invite'],
    'on_voice_state_update': ['on_voice_state_update', 'find_party_controller'],
    'on_raw_reaction_add': ['game_role_reaction_add'],
    'on_raw_reaction_remove': ['game_role_reaction_remove'],
    'on_message': ['greetings_delete_greetings', 'log_new_message', 'bolnoy_ublyudok'],
    'on_message_edit': ['log_edited_message'],
    'on_message_delete': ['log_deleted_message'],
    'on_guild_role_create': ['on_guild_role_create'],
    'on_guild_role_update': ['on_guild_role_update'],
    'on_guild_role_delete': ['on_guild_role_delete'],
    'on_guild_channel_create': ['on_guild_channel_create', 'channel_create_name_moderation'],
    'on_guild_channel_update': ['on_guild_channel_update', 'voice_name_moderation'],
    'on_guild_channel_delete': ['on_guild_channel_delete'],
    'on_member_ban': ['on_member_ban'],
    'on_member_update': ['on_member_update']
}

for event_type, handlers in listeners.items():
    if isinstance(handlers, list):
        for handler in handlers:
            bot.add_listener(globals()[handler], event_type)
    else:
        bot.add_listener(globals()[handlers], event_type)


async def run_bot(token, conn):
    retry_count = 0
    while retry_count < 3:
        try:
            await bot.start(token)
        except Exception as e:
            print(f"The bot has been stopped due to an error: {e}")
            if str(e) == "Improper token has been passed.":
                token = request_token(conn)
            else:
                os.system("python bot.py")

            retry_count += 1
            if retry_count >= 2:
                os.system("python bot.py")


async def fetch_latest_commit():
    async with aiohttp.ClientSession() as session:
        async with session.get(GITHUB_API_URL) as response:
            if response.status == 200:
                data = await response.json()
                return data['sha']
            else:
                print(f"Ошибка при доступе к GitHub API: {response.status}")
                return None

async def main():
    conn = await check_and_initialize_main_db()
    token = await get_token_from_db(conn)

    if not token:
        print("Token not found.")
        token = await request_token(conn)

    # Загружаем наше отдельное "расширение" с глобальной командой
    await bot.load_extension("Modules.safespace_commands")

    # Запускаем костыль для голосового канала (переименование каждую минуту)
    asyncio.create_task(ensure_min_voice_channels(bot))

    await run_bot(token, conn)





if __name__ == "__main__":
    asyncio.run(main())

