import asyncio
from datetime import datetime, timedelta


async def rename_kostyl_channel(bot):
    # Ждем, пока бот полностью запустится
    await bot.wait_until_ready()

    # Вычисляем, сколько осталось до начала следующего интервала кратного 10 минутам (например, 00, 10, 20, ...)
    now = datetime.utcnow() + timedelta(hours=3)  # МСК (UTC+3)
    minutes = now.minute
    remainder = minutes % 10
    delay = (10 - remainder) * 60 - now.second - now.microsecond / 1e6
    await asyncio.sleep(delay)

    while not bot.is_closed():
        guild = bot.get_guild(702588231614595172)
        if guild:
            channel = guild.get_channel(1353641396099088384)
            if channel:
                moscow_time = datetime.utcnow() + timedelta(hours=3)
                new_name = f"MEGAKOSTYL {moscow_time.strftime('%H:%M')}"
                try:
                    await channel.edit(name=new_name)
                    print(f"[MEGAKOSTYL] Канал переименован в: {new_name}")
                except Exception as e:
                    print("Ошибка при переименовании канала:", e)
        # Ждем 10 минут (600 секунд) до следующей актуализации
        await asyncio.sleep(600)
