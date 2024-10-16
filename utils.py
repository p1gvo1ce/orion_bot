import discord
from discord.ext import commands
import logging
import csv
import os
from datetime import datetime

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)

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
                writer.writerow(['Timestamp', 'Level', 'Message'])  # Заголовки
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