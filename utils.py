import discord
from discord.ext import commands
import logging
import csv
import os
import json
import requests
from datetime import datetime, timedelta, timezone
import dateparser

from Modules.phrases import get_phrase

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

class CSVHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y_%m_%d')}.csv")
        self.file_exists = os.path.isfile(self.filename)

    def emit(self, record):
        log_entry = self.format(record)
        with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not self.file_exists:
                writer.writerow(['Timestamp', 'Level', 'Message'])
                self.file_exists = True
            writer.writerow([record.asctime, record.levelname, log_entry])

csv_handler = CSVHandler()
csv_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(csv_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)


intents = discord.Intents.all()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)

def get_bot():
    return bot

def get_logger():
    return logger
def clean_channel_id(channel_id_str):
    return int(channel_id_str.replace("id", ""))

def decode_misencoded_string(input_string: str) -> str:
    try:
        return input_string.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return input_string


async def extract_fields(readable_data: str, event_type: str, guild) -> str:
    try:
        if isinstance(readable_data, str):
            data_dict = json.loads(readable_data.replace("'", "\""))
        else:
            return "Invalid data format: expected a string."

        if not isinstance(data_dict, dict):
            return "Decoded data is not a dictionary."

        if event_type == "new_message":
            channel = data_dict['message']['channel']
            category = channel.get('category', None)

            category_id = category if isinstance(category, str) else None
            channel_id = channel['id']
            author_id = data_dict['message']['author']['id']
            content = data_dict['message']['content'].replace("\\n", "\n")
            created_at = data_dict['message']['created_at']

            return (f"**{await get_phrase("Category", guild)}**: <#{category_id}>\n"
                    f"**{await get_phrase("Channel", guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase("Author", guild)}**: <@{author_id}>\n"
                    f"**{await get_phrase("Created At", guild)}**: {created_at}\n"
                    f"**{await get_phrase("Content", guild)}**:\n```{content}```")

        elif event_type == "edited_message":
            channel = data_dict['channel']
            channel_id = channel['id']
            author_id = data_dict['author']['id']
            author_name = data_dict['author']['name']
            content_before = data_dict['content_before'].replace("\\n", "\n")
            content_after = data_dict['content_after'].replace("\\n", "\n")
            edited_at = data_dict['edited_at']

            return (f"**{await get_phrase("Channel", guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase("Author", guild)}**: <@{author_id}> (Name: {author_name})\n"
                    f"**{await get_phrase("Edited At", guild)}**: {edited_at}\n"
                    f"**{await get_phrase("Content Before", guild)}**:\n```{content_before}```\n"
                    f"**{await get_phrase("Content After", guild)}**:\n```{content_after}```")

        elif event_type == "deleted_message":
            message = data_dict['message']
            channel_id = message['channel']['id']
            author_id = message['author']['id']
            author_name = message['author']['name']
            content = message['content'].replace("\\n", "\n")
            deleted_at = message['deleted_at']

            return (f"**{await get_phrase("Channel", guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase("Author", guild)}**: <@{author_id}> (Name: {author_name})\n"
                    f"**{await get_phrase("Deleted At", guild)}**: {deleted_at}\n"
                    f"**{await get_phrase("Content", guild)}**:\n```{content}```")

        elif event_type == "another_event_type":
            return (f"Some other details for event type {event_type}")

        else:
            return "Event type not recognized."

    except json.JSONDecodeError:
        return "Failed to decode readable_data. Ensure it is in the correct format."
    except Exception as e:
        return f"An error occurred: {str(e)}"


def parse_time(time_str: str, default_days_ago: int = 365) -> str:
    if time_str:
        parsed_time = dateparser.parse(time_str)
        if parsed_time:
            utc_time = parsed_time.astimezone(timezone.utc)
            return utc_time.strftime("%Y-%m-%d %H:%M:%S")

    default_time = datetime.now(timezone.utc) - timedelta(days=default_days_ago)
    return default_time.strftime("%Y-%m-%d %H:%M:%S")



def load_credentials(file_path):
    '''

    :json format:
{
  "id": "Twitch API Client ID",
  "secret": "Twitch API Client Secret Code"
}
    '''
    with open(file_path, 'r') as file:
        credentials = json.load(file)
    return credentials['id'], credentials['secret']

def get_access_token(client_id, client_secret):
    url = 'https://id.twitch.tv/oauth2/token'
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=payload)
    token = response.json().get('access_token')
    return token


def load_game_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        return {}


def save_game_data(file_path, game_data):
    with open(file_path, 'w') as file:
        json.dump(game_data, file, indent=4)


def load_game_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        return {}


def save_game_data(file_path, game_data):
    with open(file_path, 'w') as file:
        json.dump(game_data, file, indent=4)


def is_game_valid(game_name):
    file_path = 'data/games.json'
    game_name_lower = game_name.lower()

    # Загружаем данные из JSON
    game_data = load_game_data(file_path)

    # Проверяем, есть ли игра уже в JSON-файле
    if game_name in game_data:
        print(f"Результат найден в локальном файле: {game_data[game_name]}")
        return game_data[game_name] == "True"
    client_id, client_secret = load_credentials('data/twitch_api.json')
    access_token = get_access_token(client_id, client_secret)
    # Если игры нет в локальном файле, делаем запрос к API
    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    query = f'search "{game_name}"; fields name;'
    response = requests.post(url, data=query, headers=headers)

    if response.status_code == 200:
        games = response.json()
        if games:
            games = [game['name'] for game in games]
            for game in games:
                if game_name_lower == game.lower():
                    print(f"Игра найдена: {game}")

                    # Сохраняем результат в файл
                    game_data[game_name] = "True"
                    save_game_data(file_path, game_data)
                    return True

        # Если игры нет, записываем результат "False"
        print("Игра не найдена через API.")
        game_data[game_name] = "False"
        save_game_data(file_path, game_data)
        return False
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")