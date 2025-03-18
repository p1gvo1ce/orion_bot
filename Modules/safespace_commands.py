import discord
import re
from discord import app_commands
from utils import get_bot, get_logger

bot = get_bot()
logger = get_logger()


def split_text(text: str, limit=2000) -> list[str]:
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


def extract_between_backticks(text: str) -> str | None:
    """
    Ищет в строке содержимое, заключённое в одинарные бэктики `` `...` ``.
    Возвращает найденное или None, если ничего не найдено.
    """
    match = re.search(r"`([^`]+)`", text)
    if match:
        return match.group(1)
    return None


def get_description_for_channel(ch: discord.abc.GuildChannel) -> str | None:
    """
    Возвращает описание канала (строго вырезая из бэктиков),
    или None, если не удалось вытащить такое описание.

    1) ForumChannel -> смотрим ch.topic
    2) VoiceChannel -> смотрим ch.name
    3) TextChannel -> смотрим ch.topic
    4) Остальное -> не обрабатываем
    """
    # Forum
    if isinstance(ch, discord.ForumChannel):
        if ch.topic:
            return extract_between_backticks(ch.topic)
        return None

    # Voice
    elif isinstance(ch, discord.VoiceChannel):
        # В голосовом канале описание спрятано в имени
        return extract_between_backticks(ch.name)

    # Text
    elif isinstance(ch, discord.TextChannel):
        if ch.topic:
            return extract_between_backticks(ch.topic)
        return None

    # Всё, что сюда дойдёт – не обрабатываем
    return None


@bot.tree.command(name="server_navigation",
                  description="Собирает навигацию по серверу и выводит её согласно новым правилам.")
async def server_navigation(interaction: discord.Interaction):
    logger.info(f"[server_navigation] Запущена команда пользователем {interaction.user} (guild={interaction.guild})")

    guild = interaction.guild
    if guild is None:
        logger.warning("[server_navigation] Команда вызвана вне сервера (guild is None).")
        await interaction.response.send_message("Эта команда работает только на сервере.", ephemeral=True)
        return

    try:
        # Категории, которые игнорируем
        ignored_category_ids = {968539522453352458, 1032908851269349456}
        pages = []

        # 1) Каналы без категории ("General"), но только Text/Voice/Forum
        #    при этом показываем их только если получилось извлечь описание
        general_channels = sorted(
            [
                ch for ch in guild.channels
                if ch.category is None and isinstance(ch,
                                                      (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))
            ],
            key=lambda ch: ch.position
        )
        logger.info(
            f"[server_navigation] Найдено {len(general_channels)} канал(ов) без категории (не считая CategoryChannel).")

        # Собираем их в один раздел, если есть хоть один канал с норм описанием
        section_general = "## General\n"
        channels_in_general_section = 0
        for ch in general_channels:
            desc = get_description_for_channel(ch)
            if desc is None:
                # Если описания (бэктиков) нет, пропускаем
                continue
            mention = f"<#{ch.id}>"
            section_general += f"{mention}\n```\n{desc}\n```\n"
            channels_in_general_section += 1

        if channels_in_general_section > 0:
            pages.append(section_general)

        # 2) Обрабатываем категории
        categories = sorted(guild.categories, key=lambda c: c.position)
        logger.info(f"[server_navigation] Всего категорий: {len(categories)}.")

        for category in categories:
            if category.id in ignored_category_ids:
                logger.info(f"[server_navigation] Пропускаем категорию {category.name} (ID={category.id}).")
                continue

            logger.info(f"[server_navigation] Обрабатываем категорию {category.name} (ID={category.id}).")
            section = f"## {category.name}\n"
            cat_channels = sorted(category.channels, key=lambda ch: ch.position)

            channels_in_cat = 0
            for ch in cat_channels:
                if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                    desc = get_description_for_channel(ch)
                    if desc is None:
                        # Нет текста в бэктиках – пропускаем
                        continue

                    mention = f"<#{ch.id}>"
                    section += f"{mention}\n```\n{desc}\n```\n"
                    channels_in_cat += 1

            # Только если в категории есть каналы с описанием, добавляем эту страницу
            if channels_in_cat > 0:
                pages.append(section)

        # Шлём ephemeral-сообщение о запуске
        await interaction.response.send_message("Собираю навигацию по серверу…", ephemeral=True)
        logger.info("[server_navigation] Отправлено ephemeral-сообщение о начале работы.")

        # Режем каждую страницу на куски
        for idx, page in enumerate(pages, start=1):
            chunks = split_text(page, 2000)
            logger.info(f"[server_navigation] Страница {idx}/{len(pages)} -> {len(chunks)} chunk(ов).")
            for chunk in chunks:
                logger.info(f"[server_navigation] Отправляю chunk длиной {len(chunk)}.")
                await interaction.channel.send(chunk)

        await interaction.followup.send("Навигация по серверу готова!", ephemeral=True)
        logger.info("[server_navigation] Команда завершена успешно.")

    except Exception as e:
        logger.exception("[server_navigation] Произошла ошибка при формировании навигации!")
        await interaction.response.send_message(
            "Произошла ошибка при формировании навигации. Подробности в логах.",
            ephemeral=True
        )


async def setup(bot: discord.Client):
    """Пустая функция, если используешь bot.load_extension("Modules.safespace_commands")."""
    pass
