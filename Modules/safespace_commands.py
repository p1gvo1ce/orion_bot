import discord
from discord import app_commands
from discord.ext import commands
from utils import get_logger

logger = get_logger()

class SafeSpaceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="server_navigation", description="Выводит навигацию по серверу (каналы и категории).")
    async def server_navigation(self, interaction: discord.Interaction):
        """Команда собирает каналы по категориям, выводит их в виде отдельных сообщений."""

        # Сразу делаем отладочный лог
        logger.debug(f"[server_navigation] Запущена команда пользователем {interaction.user} на сервере {interaction.guild}.")

        guild = interaction.guild
        if guild is None:
            logger.warning("[server_navigation] Команда вызвана вне сервера (guild is None).")
            await interaction.response.send_message("Эта команда работает только на сервере.", ephemeral=True)
            return

        try:
            # Игнорируем некоторые категории
            ignored_category_ids = {968539522453352458, 1032908851269349456}
            pages = []

            # Сортируем каналы без категории
            general_channels = sorted(
                [ch for ch in guild.channels if ch.category is None and isinstance(ch, discord.abc.GuildChannel)],
                key=lambda ch: ch.position
            )
            logger.debug(f"[server_navigation] Найдено {len(general_channels)} канал(ов) без категории в {guild.name}.")

            # 1. Выводим "General" секцию, если есть каналы без категории
            if general_channels:
                section = "## General\n"
                for ch in general_channels:
                    mention = f"<#{ch.id}>"
                    desc = ch.topic if hasattr(ch, "topic") and ch.topic else ""
                    section += f"{mention}\n```\n{desc}\n```\n\n"
                pages.append(section)

            # 2. Проходим по категориям по их позиции
            categories = sorted(guild.categories, key=lambda c: c.position)
            logger.debug(f"[server_navigation] Всего категорий: {len(categories)}. Начинаем обход...")

            for category in categories:
                if category.id in ignored_category_ids:
                    logger.debug(f"[server_navigation] Пропускаем категорию {category.name} (ID {category.id}), она в списке игнорируемых.")
                    continue

                logger.debug(f"[server_navigation] Обрабатываем категорию: {category.name} (ID {category.id})")
                section = f"## {category.name}\n"

                # Сортируем каналы внутри категории
                cat_channels = sorted(category.channels, key=lambda ch: ch.position)
                logger.debug(f"[server_navigation] В категории {category.name} {len(cat_channels)} канал(ов).")

                for ch in cat_channels:
                    if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                        mention = f"<#{ch.id}>"
                        desc = ch.topic if hasattr(ch, "topic") and ch.topic else ""
                        section += f"{mention}\n```\n{desc}\n```\n\n"

                pages.append(section)

            # Отправляем сообщение о том, что мы начинаем
            await interaction.response.send_message("Собираю навигацию по серверу…", ephemeral=True)
            logger.debug("[server_navigation] Отправлено ephemeral-сообщение о начале.")

            # Высылаем страницы по одной
            for idx, page in enumerate(pages, start=1):
                logger.debug(f"[server_navigation] Отправляем страницу {idx}/{len(pages)} (длина текста {len(page)} символов).")
                await interaction.channel.send(page)

            # Заключительное сообщение
            await interaction.followup.send("Навигация по серверу готова!", ephemeral=True)
            logger.debug("[server_navigation] Завершили отправку навигации.")

        except Exception as e:
            # Если что-то пошло не так – логируем и пишем пользователю
            logger.exception("[server_navigation] Произошла ошибка при построении навигации!")
            await interaction.response.send_message(
                "Произошла ошибка при построении навигации. Подробности в логах.",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    """Функция, которая регистрирует Cog в боте."""
    await bot.add_cog(SafeSpaceCommands(bot))
