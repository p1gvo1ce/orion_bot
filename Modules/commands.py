from enum import member

import discord
from discord import app_commands
import random

from Modules.db_control import (write_to_guild_settings_db, delete_from_guild_settings_db, get_top_games,
                                write_to_buttons_db, write_to_members_db, read_member_data_from_db,
                                delete_member_data_from_db)
from Modules.phrases import get_phrase
from Modules.analytics import top_games_create_embed, plot_top_games, popularity_games_create_embed
from Modules.buttons import FindPartyWithoutActivity
from Modules.text_channels_control import add_game_in_game_roles_channel
from utils import get_bot

bot = get_bot()


# Создание каналов для автоматического поиска компании
@bot.tree.command(name="create_party_search_channel", description="[admin] create channels for automatic party search.")
@app_commands.describe()
@app_commands.checks.has_permissions(administrator=True)
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
    find_message_without_activity = await text_channel.send(get_phrase('Create a party search', guild))
    write_to_buttons_db(guild.id, find_message_without_activity.id, "FindPartyWithoutActivity", '{}', 12345)
    await find_message_without_activity.edit(view=FindPartyWithoutActivity(guild))

    # Отправляем сообщение о создании каналов
    await interaction.response.send_message(f"{get_phrase('channels for party search created', guild)}:\n"
                                            f"{get_phrase('Text Channel', guild)}: {text_channel.mention}\n"
                                            f"{get_phrase('Voice Channel', guild)}: {voice_channel.mention}")


# Смена языка сообщений бота
@bot.tree.command(name="language", description="[admin] change the language of bot messages.")
@app_commands.describe(lang="langeuage (ru, en)")
@app_commands.checks.has_permissions(administrator=True)
async def language(interaction: discord.Interaction, lang: str):
    langs = ['ru', 'en']
    if lang not in langs:
        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        description = (f"you need to specify the language **ru** or **en**\n"
                       "нужно указать язык **ru** или **en**")
        embed.description = description

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    else:
        delete_from_guild_settings_db(interaction.guild.id, 'language')
        write_to_guild_settings_db(interaction.guild.id, "language", lang)

        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        description = get_phrase('language_changed', interaction.guild)
        embed.description = description

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


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

# Включение и выключения автоматического удаления приветствий
@bot.tree.command(name="removing_greetings", description="[admin] Removing greetings.")
@app_commands.describe(mode="removing_greetings (on, off)", delay="Seconds (0 to off)")
@app_commands.checks.has_permissions(administrator=True)
async def language(interaction: discord.Interaction, mode: str, delay: int):
    mods = ['on', 'off']
    if mode not in mods:
        await interaction.response.send_message(get_phrase('You need to specify the on/off mode'),
                                                ephemeral=True)
    else:
        try:
            delete_from_guild_settings_db(interaction.guild.id, 'removing_greetings')
            delete_from_guild_settings_db(interaction.guild.id, 'removing_greetings_delay')
        except:
            pass
        write_to_guild_settings_db(interaction.guild.id, "removing_greetings", mode)
        write_to_guild_settings_db(interaction.guild.id, "removing_greetings_delay", delay)

        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        if mode == 'on':

            description = (f"{get_phrase('Automatic greeting deletion enabled', interaction.guild)}.\n"
                                                    f"{get_phrase('Delay', interaction.guild)} {delay} "
                                                    f"{get_phrase('seconds', interaction.guild)}.")
            embed.description = description
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        else:
            description = get_phrase('Automatic greeting deletion disabled', interaction.guild)
            embed.description = description
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

async def check_and_assign_roles(guild, top_games):
    # Проверка каждой игры из топа
    for game in top_games:
        game_name = game[0]
        role_name = game_name  # Используем имя игры как имя роли

        # Проверяем, существует ли такая роль
        role = discord.utils.get(guild.roles, name=role_name)

        # Если роли нет, создаём её с рандомным цветом
        if role is None:
            random_color = random.randint(0, 0xFFFFFF)
            role = await guild.create_role(name=role_name, color=discord.Color(random_color))
            await add_game_in_game_roles_channel({role}, guild)  # Отправляем роль в специальный канал

# Создание ролей для X популярных игр на сервере
@bot.tree.command(name="create_top_games_roles", description="[admin] create roles for top games.")
@app_commands.describe(top_count="Количество топ игр для создания ролей (например, топ 5)")
@app_commands.checks.has_permissions(administrator=True)
async def create_top_games_roles(interaction: discord.Interaction, top_count: int):
    await interaction.response.defer()  # Отложенный ответ

    guild = interaction.guild

    # Получаем топ игр за последние 30 дней с гранулярностью "день"
    top_games = get_top_games(guild.id, 30, 'day')

    # Если нет данных о топ играх
    if not top_games:
        await interaction.followup.send("Нет данных о топ играх за указанный период.", ephemeral=True)
        return

    # Оставляем только top_count самых популярных игр
    top_games = top_games[:top_count]

    try:
        # Проверяем и создаем роли для топ игр
        await check_and_assign_roles(guild, top_games)

        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        description = get_phrase('Roles for top games have been created', interaction.guild) % top_count
        embed.description = description

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )

    except Exception as e:
            await interaction.followup.send(f"Произошла ошибка: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_voice_name", description="[Global] Set a name for your personal voice channel")
@app_commands.describe(name="name for your personal voice channel")
async def set_voice_name(interaction: discord.Interaction, name: str):
    try:
        delete_member_data_from_db(interaction.user, 'voice_channel_name')
    except:
        pass
    write_to_members_db(interaction.user, 'voice_channel_name', name)

    embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
    description = get_phrase('Name_personal_voice_set', interaction.guild)
    embed.description = description

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )

@bot.tree.command(name="update_game_roles", description="[Global] Enable/disable game role update")
@app_commands.describe(mode="Mode (on, off)")
async def dont_update_roles(interaction: discord.Interaction, mode: str):
    try:
        delete_member_data_from_db(interaction.user, 'game_roles_update')
    except:
        pass
    write_to_members_db(interaction.user, 'game_roles_update', mode)

    embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
    if mode == 'on':
        description = get_phrase('Game Roles Update Enabled', interaction.guild)
    else:
        description = get_phrase('Game role update disabled', interaction.guild)
    embed.description = description

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )