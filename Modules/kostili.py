import asyncio
from datetime import datetime, timedelta

async def rename_kostyl_channel(bot):
    # Ждем, пока бот полностью запустится
    await bot.wait_until_ready()
    while not bot.is_closed():
        guild = bot.get_guild(702588231614595172)
        if guild:
            channel = guild.get_channel(1353641396099088384)
            if channel:
                # Вычисляем время по МСК (UTC+3)
                moscow_time = datetime.utcnow() + timedelta(hours=3)
                new_name = f"костыль {moscow_time.strftime('%H:%M')}"
                try:
                    await channel.edit(name=new_name)
                    print(f"[MEGAKOSTYL] Канал переименован в: {new_name}")
                except Exception as e:
                    print("Ошибка при переименовании канала:", e)
        # Пауза в 60 секунд
        await asyncio.sleep(60)
