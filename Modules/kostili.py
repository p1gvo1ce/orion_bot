import asyncio
import random
import string
from discord import VoiceChannel


async def ensure_min_voice_channels(bot):
    # Ждём, пока бот полностью запустится
    await bot.wait_until_ready()

    # Получаем категорию по ID
    category = bot.get_channel(1353976761234362369)
    if not category:
        print("Категория с ID 1353976761234362369 не найдена!")
        return

    guild = category.guild

    while not bot.is_closed():
        # Составляем список голосовых каналов в данной категории
        voice_channels = [channel for channel in guild.channels
                          if channel.category_id == category.id and isinstance(channel, VoiceChannel)]
        current_count = len(voice_channels)
        print(f"В категории '{category.name}' обнаружено {current_count} голосовых каналов.")

        if current_count < 5:
            channels_to_create = 5 - current_count
            for _ in range(channels_to_create):
                # Генерируем случайное имя: 8 символов (буквы и цифры, верхний и нижний регистр)
                random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                try:
                    new_channel = await guild.create_voice_channel(
                        name=random_name,
                        category=category
                    )
                    # Синхронизируем права канала с правами категории
                    await new_channel.edit(sync_permissions=True)
                    print(f"Создан голосовой канал '{new_channel.name}' (ID: {new_channel.id})")
                except Exception as e:
                    print("Ошибка при создании голосового канала:", e)
        # Ждем 60 секунд до следующей проверки
        await asyncio.sleep(60)
