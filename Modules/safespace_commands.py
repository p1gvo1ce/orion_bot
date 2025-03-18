import discord
from discord import app_commands
from utils import get_bot, get_logger

bot = get_bot()
logger = get_logger()

@bot.tree.command(name="server_navigation", description="Собирает навигацию по серверу и выводит её")
async def server_navigation(interaction: discord.Interaction):
    """
    Команда, которая показывает навигацию по серверу, разбивая каналы по категориям
    (голосовые, текстовые, форумы и т.д.). Работает как глобальная команда, т.к.
    не привязана к конкретному Guild ID.
    """

    logger.info(f"[server_navigation] Запущена команда пользователем {interaction.user} (guild={interaction.guild})")

    guild = interaction.guild
    if guild is None:
        logger.warning("[server_navigation] Команда вызвана вне сервера (guild is None).")
        await interaction.response.send_message("Эта команда работает только на сервере.", ephemeral=True)
        return

    try:
        # Какие категории игнорируем
        ignored_category_ids = {968539522453352458, 1032908851269349456}
        pages = []

        # 1. Каналы без категории => "General"
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

        # Шлём ephemeral-сообщение о том, что идёт сбор
        await interaction.response.send_message("Собираю навигацию по серверу…", ephemeral=True)
        logger.info("[server_navigation] Отправлено ephemeral-сообщение о начале работы.")

        # Отправляем полученные страницы в тот же канал
        for idx, page in enumerate(pages, start=1):
            logger.info(f"[server_navigation] Отправляем страницу {idx}/{len(pages)} (длина={len(page)}).")
            await interaction.channel.send(page)

        # Завершаем
        await interaction.followup.send("Навигация по серверу готова!", ephemeral=True)
        logger.info("[server_navigation] Успешно закончили отправку навигации.")

    except Exception as e:
        logger.exception("[server_navigation] Произошла ошибка при формировании навигации!")
        await interaction.response.send_message(
            "Произошла ошибка при формировании навигации. Подробности в логах.",
            ephemeral=True
        )


# Добавляем пустую функцию setup, чтобы мы могли загрузить это как расширение.
async def setup(bot: discord.Client):
    """
    Эта функция нужна, чтобы bot.load_extension('Modules.safespace_commands')
    корректно отработал. Можешь оставить её пустой, если не используешь Cogs.
    """
    pass
