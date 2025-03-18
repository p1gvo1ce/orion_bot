import discord
from discord import app_commands
from discord.ext import commands

# Команды для Safe Space – здесь можно складывать все специфичные для этого сервера команды.
class SafeSpaceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="server_navigation", description="Вывод навигации по серверу с учетом порядка категорий и каналов")
    async def server_navigation(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Эта команда работает только на сервере.", ephemeral=True)
            return

        pages = []

        # 1. Каналы без категории – группируем под "General"
        general_channels = sorted(
            [ch for ch in guild.channels if ch.category is None and isinstance(ch, discord.abc.GuildChannel)],
            key=lambda ch: ch.position
        )
        if general_channels:
            section = "## General\n"
            for ch in general_channels:
                mention = f"<#{ch.id}>"
                # Для текстовых каналов берём topic, для голосовых – может быть пусто
                desc = ch.topic if hasattr(ch, "topic") and ch.topic else ""
                section += f"{mention}\n```\n{desc}\n```\n\n"
            pages.append(section)

        # 2. Обходим все категории (по позиции) и пропускаем те, что нужно игнорировать
        ignored_category_ids = {968539522453352458, 1032908851269349456}
        categories = sorted(guild.categories, key=lambda c: c.position)
        for category in categories:
            if category.id in ignored_category_ids:
                continue
            section = f"## {category.name}\n"
            # Обрабатываем каналы внутри категории, сортируя их по позиции
            cat_channels = sorted(category.channels, key=lambda ch: ch.position)
            for ch in cat_channels:
                # Поддержка текстовых, голосовых и форумов
                if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                    mention = f"<#{ch.id}>"
                    desc = ch.topic if hasattr(ch, "topic") and ch.topic else ""
                    section += f"{mention}\n```\n{desc}\n```\n\n"
            pages.append(section)

        # Отправляем результат. Если текст слишком длинный, можно разбить на несколько сообщений.
        await interaction.response.send_message("Собираю навигацию по серверу…", ephemeral=True)
        for page in pages:
            await interaction.channel.send(page)
        await interaction.followup.send("Навигация по серверу готова!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SafeSpaceCommands(bot))
