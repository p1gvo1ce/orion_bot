import asyncio
from datetime import datetime, timedelta
import discord


async def update_megakostyl_channel(bot):
    # Ждем, пока бот полностью запустится
    await bot.wait_until_ready()

    # Ждем до ближайшего 10-минутного интервала (МСК, UTC+3)
    now = datetime.utcnow() + timedelta(hours=3)
    minutes = now.minute
    remainder = minutes % 10
    delay = (10 - remainder) * 60 - now.second - now.microsecond / 1e6
    if delay < 0:
        delay = 0
    await asyncio.sleep(delay)

    while not bot.is_closed():
        guild = bot.get_guild(702588231614595172)
        if not guild:
            print("Гильдия не найдена!")
            return

        # Получаем категорию по ID
        target_category = guild.get_channel(968539522453352458)
        if not target_category:
            print("Категория не найдена!")
            return

        # Ищем канал в этой категории, в названии которого есть "MEGAKOSTYL"
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

        # Формируем новое имя канала с актуальным временем (МСК)
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
        deletion_interval = (deletion_end - deletion_start).total_seconds() if deletion_start and deletion_end else 0
        creation_interval = (creation_end - creation_start).total_seconds() if creation_start and creation_end else 0
        total_interval = deletion_interval + creation_interval

        # Определяем цвет embed по суммарному времени
        if total_interval >= 5:
            embed_color = "#8B0000"
        elif total_interval <= 1:
            embed_color = "#00FF7F"
        else:
            embed_color = "#20B2AA"

        # Формируем embed-отчёт
        embed = discord.Embed(title="MEGAKOSTYL Update Report", color=discord.Color.from_str(embed_color))
        #embed.add_field(name="Интервал удаления", value=f"{deletion_interval:.3f} секунд", inline=False)
        #embed.add_field(name="Интервал создания", value=f"{creation_interval:.3f} секунд", inline=False)
        embed.add_field(name="Суммарное время", value=f"{total_interval:.3f} секунд\n{deletion_interval:.3f} | {creation_interval:.3f}", inline=False)
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

        # Ждем 10 минут до следующей итерации
        await asyncio.sleep(300)

async def keep_api_alive(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            # Отправляем запрос, чтобы "разбудить" API
            _ = await bot.fetch_guild(702588231614595172)
        except Exception as e:
            print("Ошибка пинга API:", e)
        await asyncio.sleep(60)  # Пингуем каждые 2 минуты