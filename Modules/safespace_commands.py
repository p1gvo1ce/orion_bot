import discord
import re
from discord import app_commands
from discord.app_commands import checks
from utils import get_bot, get_logger

bot = get_bot()
logger = get_logger()

def split_text(text: str, limit=2000) -> list[str]:
    """Разбивает text на куски не длиннее limit, стараясь резать по переводу строки."""
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
    Ищет в строке содержимое, заключённое в одинарные бэктики `...`,
    возвращает None, если не найдено.
    """
    match = re.search(r"`([^`]+)`", text)
    if match:
        return match.group(1)
    return None

def get_description_for_channel(ch: discord.abc.GuildChannel) -> str | None:
    """
    Логика извлечения описания:
    - ForumChannel: ищем бэктики в ch.topic
    - VoiceChannel: ищем бэктики в ch.name
    - TextChannel: берём весь ch.topic, если не пустой (без бэктиков)
    - Иначе None -> пропускаем
    """
    if isinstance(ch, discord.ForumChannel):
        if ch.topic:
            return extract_between_backticks(ch.topic)
        return None

    if isinstance(ch, discord.VoiceChannel):
        return extract_between_backticks(ch.name)

    if isinstance(ch, discord.TextChannel):
        return ch.topic if ch.topic else None

    return None

def mask_secret_category(name: str) -> str:
    """
    Выделяем префикс (эмодзи/знаки) и заменяем остальное на 'Секретная категория'.
    Пример: '💥Больные Ублюдки' -> '💥Секретная категория'
    """
    match = re.match(r'^([^a-zA-Zа-яА-Я0-9]+)', name)
    prefix = match.group(1) if match else ''
    return f"{prefix}Секретная категория"

@bot.tree.command(name="server_navigation", description="Собирает навигацию по серверу и выводит её (только для админов).")
@checks.has_permissions(administrator=True)
async def server_navigation(interaction: discord.Interaction):
    """
    Команда видна глобально, но при вызове проверяются права администратора.
    При отсутствии прав Discord вернёт пользователю ошибку "Missing Permissions".
    """
    logger.info(f"[server_navigation] Запущена команда пользователем {interaction.user} (guild={interaction.guild})")

    guild = interaction.guild
    if guild is None:
        logger.warning("[server_navigation] Команда вызвана вне сервера (guild is None).")
        await interaction.response.send_message("Эта команда работает только на сервере.", ephemeral=True)
        return

    try:
        # Список секретных категорий (просто пример, замени на свои ID)
        secret_category_ids = {1196415360879050842}
        # Айди категорий, которые полностью игнорируем
        ignored_category_ids = {968539522453352458, 1032908851269349456}

        pages = []

        # 1) "General" – каналы без категории (Forum / Voice / Text)
        all_general_channels = [
            ch for ch in guild.channels
            if ch.category is None and isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))
        ]
        general_channels = sorted(all_general_channels, key=lambda c: c.position)

        section_general = "## General\n"
        channels_in_general_section = 0
        for ch in general_channels:
            desc = get_description_for_channel(ch)
            if desc is None:
                continue

            mention = f"<#{ch.id}>"
            section_general += f"{mention}\n```\n{desc}\n```\n"
            channels_in_general_section += 1

        if channels_in_general_section > 0:
            pages.append(section_general)

        # 2) Проходим по категориям
        categories = sorted(guild.categories, key=lambda c: c.position)
        for category in categories:
            if category.id in ignored_category_ids:
                logger.info(f"[server_navigation] Пропускаем категорию {category.name} (ID={category.id}).")
                continue

            # Проверяем, секретная ли категория
            if category.id in secret_category_ids:
                cat_name = mask_secret_category(category.name)
            else:
                cat_name = category.name

            section = f"## {cat_name}\n"
            cat_channels = sorted(category.channels, key=lambda ch: ch.position)

            channels_in_cat = 0
            for ch in cat_channels:
                if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                    desc = get_description_for_channel(ch)
                    if desc is None:
                        continue
                    mention = f"<#{ch.id}>"
                    section += f"{mention}\n```\n{desc}\n```\n"
                    channels_in_cat += 1

            if channels_in_cat > 0:
                pages.append(section)

        # Сообщаем, что начали собирать навигацию
        await interaction.response.send_message("Собираю навигацию по серверу…", ephemeral=True)

        # Отправляем результаты
        for idx, page in enumerate(pages, start=1):
            chunks = split_text(page, 2000)
            for chunk in chunks:
                await interaction.channel.send(chunk)

        await interaction.followup.send("Навигация по серверу готова!", ephemeral=True)

    except Exception:
        logger.exception("[server_navigation] Ошибка при формировании навигации!")
        await interaction.response.send_message(
            "Произошла ошибка при формировании навигации. Смотри логи.",
            ephemeral=True
        )

async def setup(bot: discord.Client):
    pass
