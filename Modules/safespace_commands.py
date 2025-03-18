import discord
import re
from discord import app_commands
from utils import get_bot, get_logger

bot = get_bot()
logger = get_logger()

def split_text(text: str, limit=2000) -> list[str]:
    """
    Разбивает text на куски не длиннее limit.
    Старается резать по последнему '\n' до limit, чтобы не обрубать фрагмент посередине строки.
    """
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
    Ищет в строке содержимое, заключённое в одинарные бэктики: `...`
    Возвращает найденное или None, если ничего не найдено.
    """
    match = re.search(r"`([^`]+)`", text)
    if match:
        return match.group(1)
    return None

def get_description_for_channel(ch: discord.abc.GuildChannel) -> str | None:
    """
    Возвращает описание канала по логике:
      - ForumChannel: берем text из ch.topic, ищем в нем бэктики. Если нет бэктиков — None (пропускаем).
      - VoiceChannel: берем text из ch.name, ищем в нем бэктики. Если нет бэктиков — None.
      - TextChannel: берем весь ch.topic целиком (если оно есть). Если ch.topic пустой/нет — None.
      - Остальные типы каналов пропускаем (None).
    """

    if isinstance(ch, discord.ForumChannel):
        # Описание из ch.topic в бэктиках
        if ch.topic:
            desc = extract_between_backticks(ch.topic)
            return desc  # Может быть None, если бэктиков нет
        return None

    elif isinstance(ch, discord.VoiceChannel):
        # Описание в имени канала, ищем бэктики
        desc = extract_between_backticks(ch.name)
        return desc

    elif isinstance(ch, discord.TextChannel):
        # Показываем весь topic, если есть. Без бэктиков
        if ch.topic:
            return ch.topic
        return None

    # Остальные типы (CategoryChannel, StageChannel, и т.д.) не нужны
    return None

@bot.tree.command(name="server_navigation", description="Собирает навигацию по серверу и выводит её по заданным правилам")
async def server_navigation(interaction: discord.Interaction):
    logger.info(f"[server_navigation] Запущена команда пользователем {interaction.user} (guild={interaction.guild})")

    guild = interaction.guild
    if guild is None:
        logger.warning("[server_navigation] Команда вызвана вне сервера (guild is None).")
        await interaction.response.send_message("Эта команда работает только на сервере.", ephemeral=True)
        return

    try:
        ignored_category_ids = {968539522453352458, 1032908851269349456}
        pages = []

        # Сначала собираем каналы без категории: Forum / Voice / Text
        all_general_channels = [
            ch for ch in guild.channels
            if ch.category is None and isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))
        ]
        general_channels = sorted(all_general_channels, key=lambda ch: ch.position)

        logger.info(f"[server_navigation] Найдено {len(general_channels)} канал(ов) без категории (Forum/Voice/Text).")

        section_general = "## General\n"
        channels_in_general_section = 0
        for ch in general_channels:
            desc = get_description_for_channel(ch)
            if desc is None:
                # Если не получилось извлечь (либо пустое, либо без бэктиков), пропускаем
                continue

            mention = f"<#{ch.id}>"
            section_general += f"{mention}\n```\n{desc}\n```\n"
            channels_in_general_section += 1

        if channels_in_general_section > 0:
            pages.append(section_general)

        # Теперь проходимся по категориям
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
                        continue

                    mention = f"<#{ch.id}>"
                    section += f"{mention}\n```\n{desc}\n```\n"
                    channels_in_cat += 1

            # Если в категории нашлись каналы с описанием, добавляем эту секцию
            if channels_in_cat > 0:
                pages.append(section)

        await interaction.response.send_message("Собираю навигацию по серверу…", ephemeral=True)
        logger.info("[server_navigation] Отправлено ephemeral-сообщение о начале работы.")

        # Каждую «страницу» режем на куски по 2000 символов
        for idx, page in enumerate(pages, start=1):
            chunks = split_text(page, 2000)
            logger.info(f"[server_navigation] Страница {idx}/{len(pages)} -> {len(chunks)} chunk(ов).")
            for chunk in chunks:
                logger.info(f"[server_navigation] Отправляю chunk длиной {len(chunk)} символов.")
                await interaction.channel.send(chunk)

        await interaction.followup.send("Навигация по серверу готова!", ephemeral=True)
        logger.info("[server_navigation] Команда завершена успешно.")

    except Exception:
        logger.exception("[server_navigation] Произошла ошибка при формировании навигации!")
        await interaction.response.send_message(
            "Произошла ошибка при формировании навигации. Подробности смотри в логах.",
            ephemeral=True
        )

async def setup(bot: discord.Client):
    """Если используешь bot.load_extension('Modules.safespace_commands')"""
    pass
