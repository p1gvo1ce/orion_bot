import tracemalloc
import asyncio
import os
import git  # Импортируем библиотеку для работы с Git

from utils import get_bot
bot = get_bot()
from Modules.db_control import (check_and_initialize_main_db, get_token_from_db, request_token)
from Modules.buttons import update_buttons_on_start
from Modules.commands import (create_party_search_channel, game_popularity_chart, top_games_command, language,
                              create_top_games_roles, set_voice_name, dont_update_roles, set_utc_time, logging_system,
                              get_logs)
from Modules.voice_channels_control import find_party_controller
from Modules.role_control import game_role_reaction_add, game_role_reaction_remove
from Modules.events import bot_start, join_from_invite, greetings_delete_greetings, start_copy_logs_to_analytics
from Modules.logger import log_new_message, log_edited_message, log_deleted_message

tracemalloc.start()

listeners = {
    'on_ready': ['bot_start', 'start_copy_logs_to_analytics'],
    'on_member_join': ['join_from_invite'],
    'on_voice_state_update': ['find_party_controller'],
    'on_raw_reaction_add': ['game_role_reaction_add'],
    'on_raw_reaction_remove': ['game_role_reaction_remove'],
    'on_message': ['greetings_delete_greetings', 'log_new_message'],
    'on_message_edit': ['log_edited_message'],
    'on_message_delete': ['log_deleted_message']
}

for event_type, handlers in listeners.items():
    if isinstance(handlers, list):
        for handler in handlers:
            bot.add_listener(globals()[handler], event_type)
    else:
        bot.add_listener(globals()[handlers], event_type)

async def update_code(repo_path):
    try:
        repo = git.Repo(repo_path)
        origin = repo.remotes.origin
        origin.pull()  # Получение обновлений
        print("Код обновлен из репозитория.")
        return True  # Обновление прошло успешно
    except Exception as e:
        print(f"Ошибка при обновлении кода: {e}")
        return False  # Обновление не удалось

async def run_bot(token, conn):
    repo_path = '/path/to/your/local/repo'  # Замените на путь к вашему локальному репозиторию
    retry_count = 0
    while retry_count < 3:
        try:
            await bot.start(token)
        except Exception as e:
            print(f"The bot has been stopped due to an error: {e}")
            if str(e) == "Improper token has been passed.":
                token = request_token(conn)
            else:
                if await update_code(repo_path):  # Проверяем обновления перед перезапуском
                    os.system("python bot.py")  # Перезапускаем бот

            retry_count += 1
            if retry_count >= 2:
                os.system("python bot.py")

async def check_for_updates(repo_path):
    await bot.wait_until_ready()
    while not bot.is_closed():
        if await update_code(repo_path):  # Проверяем обновления каждую минуту
            os.system("python bot.py")  # Перезапускаем бот после обновления
        await asyncio.sleep(60)  # Проверяем каждую минуту

async def main():
    conn = await check_and_initialize_main_db()
    token = await get_token_from_db(conn)

    if not token:
        print("Token not found.")
        token = await request_token(conn)

    # Запускаем задачу асинхронно
    asyncio.create_task(check_for_updates('/path/to/your/local/repo'))  # Замените на путь к вашему локальному репозиторию
    await run_bot(token, conn)

if __name__ == "__main__":
    asyncio.run(main())

