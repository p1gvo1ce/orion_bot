import discord
import re
from discord import app_commands
from utils import get_bot, get_logger

bot = get_bot()
logger = get_logger()

def split_text(text, limit=2000):
    """Разбивает текст на части не длиннее limit символов, стараясь резать по переводу строки."""
    chunks = []
    while len(text) > limit:
        split_point = text.rfind('\n', 0, limit)
        if split_point == -1:
            split_point = limit
        chunks.append(text[:split_point])
        text = text[split_point:]
    if text:
        chunks.append(text)
    return chunks

def extract_forum_description(desc: str) -> str:
    """
    Если в описании форума (topic) есть текст в одинарных бэктиках, берём только его.
    Иначе возвращаем исходное описание.
    """
    match = re.search(r"`([^`]+)`", desc)
    if match:
        return match.group(1)
    return desc

@bot.tree.command(name="server_navigation", description="Собирает навигацию по серверу и выводит её.")
async def server_navigation(interaction: discord.Interaction):
    logger.debug(f"[server_navigation] Запущена команда пользователем {interaction.user} (guild={interaction.guild})")

    guild = interaction.guild
    if guild is None:
        logger.warning("[server_navigation] Команда вызвана вне сервера (guild is None).")
        await interaction.response.send_message("Эта команда работает только на сервере.", ephemeral=True)
        return

    try:
        ignored_category_ids = {968539522453352458, 1032908851269349456}
        pages = []

        # Собираем каналы без категории (General), исключая CategoryChannel
        general_channels = sorted(
            [
                ch for ch in guild.channels
                if ch.category is None and isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))
            ],
            key=lambda ch: ch.position
        )
        logger.debug(f"[server_navigation] Найдено {len(general_channels)} канал(ов) без категории (не считая CategoryChannel).")

        if general_channels:
            section = "## General\n"
            for ch in general_channels:
                mention = f"<#{ch.id}>"

                # По умолчанию описание пустое
                desc = ""

                # Проверяем, есть ли у объекта атрибут .topic
                if hasattr(ch, "topic") and ch.topic:
                    desc = ch.topic

                # Если форум – извлекаем кусок описания из обратных кавычек
                if isinstance(ch, discord.ForumChannel):
                    desc = extract_forum_description(desc)

                section += f"{mention}\n```\n{desc}\n```\n"
            pages.append(section)

        # Обрабатываем категории
        categories = sorted(guild.categories, key=lambda c: c.position)
        logger.debug(f"[server_navigation] Всего категорий: {len(categories)}.")
        for category in categories:
            if category.id in ignored_category_ids:
                logger.debug(f"[server_navigation] Пропускаем категорию {category.name} (ID={category.id}).")
                continue

            logger.debug(f"[server_navigation] Обрабатываем категорию {category.name} (ID={category.id}).")
            section = f"## {category.name}\n"
            cat_channels = sorted(category.channels, key=lambda ch: ch.position)

            for ch in cat_channels:
                if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                    mention = f"<#{ch.id}>"

                    desc = ""
                    if hasattr(ch, "topic") and ch.topic:
                        desc = ch.topic

                    # Если это форум – извлекаем кусок описания из обратных кавычек
                    if isinstance(ch, discord.ForumChannel):
                        desc = extract_forum_description(desc)

                    section += f"{mention}\n```\n{desc}\n```\n"

            pages.append(section)

        # Отправляем ephemeral-уведомление
        await interaction.response.send_message("Собираю навигацию по серверу…", ephemeral=True)
        logger.debug("[server_navigation] Отправлено ephemeral-сообщение о начале работы.")

        # Отправляем каждую страницу, разбивая если >2000 символов
        for idx, page in enumerate(pages, start=1):
            chunks = split_text(page, 2000)
            logger.debug(f"[server_navigation] Страница {idx}/{len(pages)} -> {len(chunks)} chunk(ов).")
            for chunk in chunks:
                logger.debug(f"[server_navigation] Отправляю chunk длиной {len(chunk)}.")
                await interaction.channel.send(chunk)

        await interaction.followup.send("Навигация по серверу готова!", ephemeral=True)
        logger.debug("[server_navigation] Команда завершена успешно.")

    except Exception as e:
        logger.exception("[server_navigation] Произошла ошибка при формировании навигации!")
        await interaction.response.send_message(
            "Произошла ошибка при формировании навигации. Подробности в логах.",
            ephemeral=True
        )

async def setup(bot: discord.Client):
    """Пустая функция для bot.load_extension, если используешь расширения."""
    pass
