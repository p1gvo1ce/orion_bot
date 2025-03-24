import asyncio
from datetime import datetime, timedelta
import discord


async def update_megakostyl_channel(bot):
    # Ждем, пока бот полностью запустится
    await bot.wait_until_ready()

    # Вычисляем, сколько осталось до ближайшего интервала кратного 10 минутам (МСК время UTC+3)
    now = datetime.utcnow() + timedelta(hours=3)
    minutes = now.minute
    remainder = minutes % 10
    delay = (10 - remainder) * 60 - now.second - now.microsecond / 1e6
    if delay < 0:
        delay = 0
    await asyncio.sleep(delay)

    guild = bot.get_guild(702588231614595172)
    if not guild:
        print("Гильдия не найдена!")
        return

    # Получаем категорию по ID
    target_category = guild.get_channel(968539522453352458)
    if not target_category:
        print("Категория не найдена!")
        return

    # Ищем канал в этой категории, в названии которого есть слово "MEGAKOSTYL"
    target_channel = None
    for channel in guild.channels:
        if channel.category_id == 968539522453352458 and "MEGAKOSTYL" in channel.name:
            target_channel = channel
            break

    deletion_start = None
    deletion_end = None
    creation_start = None
    creation_end = None

    if target_channel:
        deletion_start = datetime.utcnow()
        try:
            await target_channel.delete()
            deletion_end = datetime.utcnow()
            print(f"[MEGAKOSTYL] Удалён канал {target_channel.id}")
        except Exception as e:
            print("Ошибка при удалении канала:", e)
    else:
        print("Канал с 'MEGAKOSTYL' не найден в категории.")

    # Формируем новое имя канала
    moscow_time = datetime.utcnow() + timedelta(hours=3)
    new_channel_name = f"MEGAKOSTYL {moscow_time.strftime('%H:%M')}"

    # Настраиваем пермишены: скрыть канал от всех, кроме роли с ID 923183831094284318
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.get_role(923183831094284318): discord.PermissionOverwrite(view_channel=True)
    }

    creation_start = datetime.utcnow()
    try:
        new_channel = await guild.create_voice_channel(
            new_channel_name,
            category=target_category,
            overwrites=overwrites
        )
        creation_end = datetime.utcnow()
        print(f"[MEGAKOSTYL] Создан канал {new_channel.id} с именем '{new_channel.name}'")
    except Exception as e:
        print("Ошибка при создании канала:", e)

    # Вычисляем интервалы
    deletion_interval = (deletion_end - deletion_start).total_seconds() if deletion_start and deletion_end else None
    creation_interval = (creation_end - creation_start).total_seconds() if creation_start and creation_end else None

    # Формируем embed-отчёт
    embed = discord.Embed(title="MEGAKOSTYL Update Report", color=discord.Color.blue())
    embed.add_field(name="Новое имя канала", value=new_channel_name, inline=False)
    if deletion_interval is not None:
        embed.add_field(name="Интервал удаления", value=f"{deletion_interval:.3f} секунд", inline=False)
    else:
        embed.add_field(name="Интервал удаления", value="Канал не найден", inline=False)
    if creation_interval is not None:
        embed.add_field(name="Интервал создания", value=f"{creation_interval:.3f} секунд", inline=False)
    else:
        embed.add_field(name="Интервал создания", value="Ошибка создания", inline=False)
    embed.timestamp = datetime.utcnow()

    # Отправляем embed в текстовый канал с ID 1353656805116477530
    report_channel = guild.get_channel(1353656805116477530)
    if report_channel:
        try:
            await report_channel.send(embed=embed)
        except Exception as e:
            print("Ошибка отправки отчёта:", e)
    else:
        print("Текстовый канал для отчётов не найден.")
