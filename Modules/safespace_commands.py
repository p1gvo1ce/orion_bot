import discord
from discord import app_commands
from utils import get_bot, get_logger

bot = get_bot()
logger = get_logger()

def split_text(text, limit=2000):
    """Разбивает текст на части не длиннее limit символов, пытаясь разрезать по переводу строки."""
    chunks = []
    while len(text) > limit:
        # Ищем последний перевод строки в пределах limit символов
        split_point = text.rfind('\n', 0, limit)
        if split_point == -1:
            split_point = limit
        chunks.append(text[:split_point])
        text = text[split_point:]
    if text:
        chunks.append(text)
    return chunks

@bot.tree.command(name="server_navigation", description="Собирает навигацию по серверу и выводит её")
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

        # 1. Собираем каналы без категории (General)
        general_channels = sorted(
            [ch for ch in guild.channels if ch.category is None and isinstance(ch, discord.abc.GuildChannel)],
            key=lambda ch: ch.position
        )
        logger.info(f"[server_navigation] Найдено {len(general_channels)} канал(ов) без категории.")
        if general_channels:
            section = "## General\n"
            for ch in general_channels:
                mention = f"<#{ch.id}>"
                desc = ch.topic if hasattr(ch, "topic") and ch.topic else ""
                section += f"{mention}\n```\n{desc}\n```\n\n"
            pages.append(section)

        # 2. Обходим категории по позиции
        categories = sorted(guild.categories, key=lambda c: c.position)
        logger.info(f"[server_navigation] Всего категорий: {len(categories)}.")
        for category in categories:
            if category.id in ignored_category_ids:
                logger.info(f"[server_navigation] Пропускаем категорию {category.name} (ID={category.id}).")
                continue
            logger.info(f"[server_navigation] Обрабатываем категорию {category.name} (ID={category.id}).")
            section = f"## {category.name}\n"
            cat_channels = sorted(category.channels, key=lambda ch: ch.position)
            for ch in cat_channels:
                if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                    mention = f"<#{ch.id}>"
                    desc = ch.topic if hasattr(ch, "topic") and ch.topic else ""
                    section += f"{mention}\n```\n{desc}\n```\n\n"
            pages.append(section)

        await interaction.response.send_message("Собираю навигацию по серверу…", ephemeral=True)
        logger.info("[server_navigation] Отправлено ephemeral-сообщение о начале работы.")

        # Отправляем каждую страницу, разбивая на чанки если превышает лимит
        for idx, page in enumerate(pages, start=1):
            chunks = split_text(page, 2000)
            logger.info(f"[server_navigation] Страница {idx}/{len(pages)} делится на {len(chunks)} часть(ей).")
            for chunk in chunks:
                logger.info(f"[server_navigation] Отправляю chunk длиной {len(chunk)} символов.")
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
    # Функция setup нужна для загрузки расширения через bot.load_extension
    pass
