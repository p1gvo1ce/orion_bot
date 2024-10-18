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
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

class CSVHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y_%m_%d')}.csv")
        self.file_exists = os.path.isfile(self.filename)
        self.file = open(self.filename, mode='a', newline='', encoding='utf-8')  # Открываем файл заранее
        self.writer = csv.writer(self.file)
        if not self.file_exists:
            self.writer.writerow(['Timestamp', 'Level', 'Message'])
            self.file_exists = True

    def emit(self, record):
        log_entry = self.format(record)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.writer.writerow([timestamp, record.levelname, log_entry])
        self.file.flush()  # Обязательно сбрасываем буфер

    def close(self):
        self.file.close()  # Закрываем файл при завершении работы
        super().close()

# Настройка логгера
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

csv_handler = CSVHandler()
csv_handler.setFormatter(logging.Formatter('%(message)s'))
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

            return (f"**{await get_phrase('Category', guild)}**: <#{category_id}>\n"
                    f"**{await get_phrase('Channel', guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase('Author', guild)}**: <@{author_id}>\n"
                    f"**{await get_phrase('Created At', guild)}**: {created_at}\n"
                    f"**{await get_phrase('Content', guild)}**:\n```{content}```")

        elif event_type == "edited_message":
            channel = data_dict['channel']
            channel_id = channel['id']
            author_id = data_dict['author']['id']
            author_name = data_dict['author']['name']
            content_before = data_dict['content_before'].replace("\\n", "\n")
            content_after = data_dict['content_after'].replace("\\n", "\n")
            edited_at = data_dict['edited_at']

            return (f"**{await get_phrase('Channel', guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase('Author', guild)}**: <@{author_id}> (Name: {author_name})\n"
                    f"**{await get_phrase('Edited At', guild)}**: {edited_at}\n"
                    f"**{await get_phrase('Content Before', guild)}**:\n```{content_before}```\n"
                    f"**{await get_phrase('Content After', guild)}**:\n```{content_after}```")

        elif event_type == "deleted_message":
            message = data_dict['message']
            channel_id = message['channel']['id']
            author_id = message['author']['id']
            author_name = message['author']['name']
            content = message['content'].replace("\\n", "\n")
            deleted_at = message['deleted_at']

            return (f"**{await get_phrase('Channel', guild)}**: <#{channel_id}>\n"
                    f"**{await get_phrase('Author', guild)}**: <@{author_id}> (Name: {author_name})\n"
                    f"**{await get_phrase('Deleted At', guild)}**: {deleted_at}\n"
                    f"**{await get_phrase('Content', guild)}**:\n```{content}```")

        elif event_type == "member_joined":
            member = data_dict['member']
            inviter_id = member['inviter']['id']
            invite_code = member['invite_code']
            member_name = member['name']
            member_discriminator = member['discriminator']
            joined_at = member['joined_at']

            return (f"**{await get_phrase('Member', guild)}**: {member_name}#{member_discriminator} <@{member['id']}>\n"
                    f"**{await get_phrase('Invited by', guild)}**: <@{inviter_id}>\n"
                    f"**{await get_phrase('Invite Code', guild)}**: `{invite_code}`\n"
                    f"**{await get_phrase('Joined At', guild)}**: {joined_at}\n")

        elif event_type == "member_left":
            member = data_dict['member']
            member_name = member['name']
            member_discriminator = member['discriminator']
            left_at = member['left_at']

            return (f"**{await get_phrase('Member', guild)}**: {member_name}#{member_discriminator} <@{member['id']}>\n"
                    f"**{await get_phrase('Left At', guild)}**: {left_at}\n")

        elif event_type == "member_muted":
            member = data_dict['member']
            reason = member['reason']
            duration = member['duration']
            muted_at = member['muted_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Muted At', guild)}**: {muted_at}\n"
                f"**{await get_phrase('Reason', guild)}**: {reason or await get_phrase('No reason provided', guild)}\n"
                f"**{await get_phrase('Duration', guild)}**: {duration or await get_phrase('Indefinite', guild)}\n")

        elif event_type == "member_unmuted":
            member = data_dict['member']
            reason = member['reason']
            unmuted_at = member['unmuted_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Unmuted At', guild)}**: {unmuted_at}\n"
                f"**{await get_phrase('Reason', guild)}**: {reason or await get_phrase('No reason provided', guild)}\n"
            )

        elif event_type == "member_banned":
            member = data_dict['member']
            reason = member['reason']
            banned_at = member['banned_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Banned At', guild)}**: {banned_at}\n"
                f"**{await get_phrase('Reason', guild)}**: {reason or await get_phrase('No reason provided', guild)}\n")

        elif event_type == "voice_joined":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            joined_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Joined Voice Channel', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Joined At', guild)}**: {joined_at}\n"
            )

        elif event_type == "voice_left":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            left_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Left Voice Channel', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Left At', guild)}**: {left_at}\n"
            )

        elif event_type == "voice_switched":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            switched_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Switched Voice Channels', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Switched At', guild)}**: {switched_at}\n"
            )

        elif event_type == "voice_mute":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            muted_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Muted Microphone', guild)}**\n"
                f"**{await get_phrase('Voice Channel', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Muted At', guild)}**: {muted_at}\n"
            )

        elif event_type == "voice_deaf":
            member = data_dict['member']
            voice_channel = data_dict['event']['channel']
            deafened_at = data_dict['event']['occurred_at']

            return (
                f"**{await get_phrase('Member', guild)}**: {member['name']}#{member['discriminator']} <@{member['id']}>\n"
                f"**{await get_phrase('Deafened', guild)}**\n"
                f"**{await get_phrase('Voice Channel', guild)}**: {voice_channel['name']}\n"
                f"**{await get_phrase('Deafened At', guild)}**: {deafened_at}\n"
            )

        elif event_type == "role_created":
            role = data_dict['role']
            return (f"**{await get_phrase('Role', guild)}**: {role['name']} (ID: {role['id']})\n"
                    f"**{await get_phrase('Created At', guild)}**: {role['created_at']}\n")

        elif event_type == "role_deleted":
            role = data_dict['role']
            return (f"**{await get_phrase('Role', guild)}**: {role['name']} (ID: {role['id']})\n"
                    f"**{await get_phrase('Deleted At', guild)}**: {role['deleted_at']}\n")

        elif event_type == "role_updated":
            before_role = data_dict['before']
            after_role = data_dict['after']
            return (f"**{await get_phrase('Role Updated', guild)}**\n"
                    f"**{await get_phrase('Before', guild)}**: {before_role['name']} (ID: {before_role['id']})\n"
                    f"**{await get_phrase('After', guild)}**: {after_role['name']} (ID: {after_role['id']})\n")

        elif event_type == "channel_created":
            channel = data_dict['channel']
            return (f"**{await get_phrase('Channel', guild)}**: {channel['name']} (ID: {channel['id']})\n"
                    f"**{await get_phrase('Created At', guild)}**: {channel['created_at']}\n")

        elif event_type == "channel_deleted":
            channel = data_dict['channel']
            return (f"**{await get_phrase('Channel', guild)}**: {channel['name']} (ID: {channel['id']})\n"
                    f"**{await get_phrase('Deleted At', guild)}**: {channel['deleted_at']}\n")

        elif event_type == "channel_updated":
            before_channel = data_dict['before']
            after_channel = data_dict['after']
            return (f"**{await get_phrase('Channel Updated', guild)}**\n"
                    f"**{await get_phrase('Before', guild)}**: {before_channel['name']} (ID: {before_channel['id']})\n"
                    f"**{await get_phrase('After', guild)}**: {after_channel['name']} (ID: {after_channel['id']})\n")




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
    abs_file_path = os.path.join(os.path.dirname(__file__), file_path)
    with open(abs_file_path, 'r') as file:
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
    file_path = 'Data/games.json'
    game_name_lower = game_name.lower()

    # Загружаем данные из JSON
    game_data = load_game_data(file_path)

    # Проверяем, есть ли игра уже в JSON-файле
    if game_name in game_data:
        print(f"Результат найден в локальном файле: {game_data[game_name]}")
        return game_data[game_name] == "True"
    client_id, client_secret = load_credentials('Data/twitch_api.json')
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