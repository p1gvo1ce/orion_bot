import discord
from discord import app_commands
from discord.ext import commands
from utils import get_bot

# Этот Cog содержит команды для сервера Safe Space.
# Здесь можно добавлять и другие команды, специфичные для этого сервера.
class SafeSpaceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="server_navigation", description="Показывает навигацию по серверу Safe Space")
    async def server_navigation(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Эта команда работает только на сервере.", ephemeral=True)
            return

        # Игнорируем категории с этими ID, пускай они остаются в стороне.
        ignored_category_ids = {968539522453352458, 1032908851269349456}

        pages = []  # Список страниц навигации

        # Каналы без категории группируем под заголовком General.
        general_channels = [
            ch for ch in guild.channels
            if ch.category is None and isinstance(ch, (discord.TextChannel, discord.VoiceChannel))
        ]
        if general_channels:
            content = "## General\n"
            # Здесь мы используем topic канала как описание, если оно задано.
            for ch in general_channels:
                desc = ch.topic if hasattr(ch, "topic") and ch.topic else ""
                content += f"<#{ch.id}>\n```\n{desc}\n```\n\n"
            pages.append(content)

        # Проходим по всем категориям в порядке, соответствующем их позиции.
        categories = sorted(guild.categories, key=lambda c: c.position)
        for category in categories:
            if category.id in ignored_category_ids:
                continue  # Игнорируем ненужные категории
            content = f"## {category.name}\n"
            for ch in sorted(category.channels, key=lambda c: c.position):
                if isinstance(ch, (discord.TextChannel, discord.VoiceChannel)):
                    desc = ch.topic if hasattr(ch, "topic") and ch.topic else ""
                    content += f"<#{ch.id}>\n```\n{desc}\n```\n\n"
            pages.append(content)

        # Отправляем каждую страницу в канал.
        await interaction.response.send_message("Готовлю навигацию по серверу, подожди...", ephemeral=True)
        for page in pages:
            await interaction.channel.send(page)
        await interaction.followup.send("Навигация по серверу готова.", ephemeral=True)

    # Здесь можно добавить другие команды для Safe Space.
    # Например, команда для получения актуальной информации о сервере,
    # настройки специальных уведомлений и т.п.

# Функция для регистрации Cog в боте.
async def setup(bot: commands.Bot):
    await bot.add_cog(SafeSpaceCommands(bot))
