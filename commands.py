import discord
from discord import app_commands
from discord.ext import commands

from DataBase.db_control import write_to_guild_settings_db, delete_from_guild_settings_db, get_top_games
from phrases import get_phrase
from Analytics.analytics import top_games_create_embed, plot_top_games, popularity_games_create_embed
from utils import get_bot

bot = get_bot()


# Создание каналов для автоматического поиска компании
@bot.tree.command(name="create_party_search_channel", description="[admin] create channels for automatic party search.")
@app_commands.describe()
@commands.has_permissions(administrator=True)
async def create_party_search_channel(interaction: discord.Interaction):
    guild = interaction.guild  # Получаем объект сервера (гильдии)

    # Создаем текстовый канал для поиска группы
    text_channel = await guild.create_text_channel('party-search-text')

    # Создаем голосовой канал для поиска группы
    voice_channel = await guild.create_voice_channel('party-search-voice')

    # ID созданных каналов и ID сервера
    text_channel_id = text_channel.id
    voice_channel_id = voice_channel.id
    guild_id = guild.id

    # Записываем информацию в базу данных
    write_to_guild_settings_db(guild_id, "party_find_text_channel_id", f"id{text_channel_id}")
    write_to_guild_settings_db(guild_id, "party_find_voice_channel_id", f"id{voice_channel_id}")

    # Отправляем сообщение о создании каналов
    await interaction.response.send_message(f"{get_phrase('channels for party search created', guild)}:\n"
                                            f"{get_phrase('Text Channel', guild)}: {text_channel.mention}\n"
                                            f"{get_phrase('Voice Channel', guild)}: {voice_channel.mention}")


# Смена языка сообщений бота
@bot.tree.command(name="language", description="[admin] change the language of bot messages.")
@app_commands.describe(lang="langeuage (ru, en)")
@commands.has_permissions(administrator=True)
async def language(interaction: discord.Interaction, lang: str):
    langs = ['ru', 'en']
    if lang not in langs:
        await interaction.response.send_message(f"you need to specify the language **ru** or **en**\n"
                                                "нужно указать язык **ru** или **en**",
                                                ephemeral=True)
    else:
        delete_from_guild_settings_db(interaction.guild.id, 'language')
        write_to_guild_settings_db(interaction.guild.id, "language", lang)

        await interaction.response.send_message(get_phrase('language_changed', interaction.guild), ephemeral=True)


# Получение анализа самых популярных игр на сервере
@bot.tree.command(name="top_games", description="Get top games for the last N days.")
@app_commands.describe(days="Number of days to analyze", top="Number of top games", granularity="Granularity (day, week, month)")

async def top_games_command(interaction: discord.Interaction, days: int, top: int, granularity: str):
    guild_id = interaction.guild_id
    top_games = get_top_games(guild_id, days, granularity)
    top_games = top_games[:top]

    graph_buf = plot_top_games(interaction.guild, top_games, days, granularity)

    embed = top_games_create_embed(top_games, days, granularity, interaction.guild)

    file = discord.File(fp=graph_buf, filename="top_games.png")
    embed.set_image(url="attachment://top_games.png")
    await interaction.response.send_message(embed=embed, file=file)

# Получение графика популярности игры на сервере
@bot.tree.command(name="game_popularity_chart", description="Get game popularity chart for the last N days.")
@app_commands.describe(days="Number of days to analyze", granularity="Granularity (day, week, month)", game="Name of the game")

async def game_popularity_chart(interaction: discord.Interaction, days: int, granularity: str, game: str):

    graph_buf = plot_top_games(interaction.guild, [], days, granularity, game)

    embed = popularity_games_create_embed(game, days, granularity, interaction.guild)

    file = discord.File(fp=graph_buf, filename=f"{game}_popularity.png")
    embed.set_image(url=f"attachment://{game}_popularity.png")
    await interaction.response.send_message(embed=embed, file=file)