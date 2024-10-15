import discord
from discord.ext import commands

intents = discord.Intents.all()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)


def get_bot():
    global bot
    return bot

def clean_channel_id(channel_id_str):
    # Убираем префикс 'id' и приводим к целому числу
    return int(channel_id_str.replace("id", ""))