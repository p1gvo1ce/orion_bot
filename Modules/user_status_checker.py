import asyncio
from datetime import datetime, timedelta
import discord

WATCHED_USER_ID = 1023342605322436678
TARGET_USER_ID = 469306021106417664
GUILD_ID = 702588231614595172

CHECK_INTERVAL_SECONDS = 60  # раз в минуту проверяем
SEND_INTERVAL_SECONDS = 3600  # отправлять не чаще одного раза в час

last_sent_time = None  # время последней отправки


async def check_user_status(bot):
    global last_sent_time

    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print(f"Guild {GUILD_ID} not found.")
        return

    while not bot.is_closed():
        member = guild.get_member(WATCHED_USER_ID)
        if member:
            status = member.status
            print(status)
            # Не оффлайн
            if status != discord.Status.offline:
                now = datetime.utcnow()
                if not last_sent_time or (now - last_sent_time) > timedelta(seconds=SEND_INTERVAL_SECONDS):
                    try:
                        target_user = guild.get_member(TARGET_USER_ID)
                        if target_user:
                            await target_user.send(f"Статус пользователя {member.name} сейчас: {status.name}")
                            print(f"Отправлено сообщение о статусе {status.name} пользователю {target_user.name}")
                            last_sent_time = now
                        else:
                            print(f"Пользователь для отправки сообщений (ID {TARGET_USER_ID}) не найден на сервере.")
                    except Exception as e:
                        print(f"Ошибка при отправке статуса: {e}")
        else:
            print(f"Пользователь для отслеживания (ID {WATCHED_USER_ID}) не найден на сервере.")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
