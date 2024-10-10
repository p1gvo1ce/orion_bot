
bot = None

def send_bot(bot_from_main):
    global bot
    bot = bot_from_main

def get_bot():
    global bot
    return bot

def clean_channel_id(channel_id_str):
    # Убираем префикс 'id' и приводим к целому числу
    return int(channel_id_str.replace("id", ""))