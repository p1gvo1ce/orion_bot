from enum import member
import discord
from discord import app_commands
import random
import json
from datetime import datetime, timedelta

from Modules.db_control import (write_to_guild_settings_db, delete_from_guild_settings_db, get_top_games,
                                write_to_buttons_db, write_to_members_db, read_logs_from_analytics,
                                delete_member_data_from_db, read_from_guild_settings_db)
from Modules.phrases import get_phrase
from Modules.analytics import top_games_create_embed, plot_top_games, popularity_games_create_embed
from Modules.buttons import FindPartyWithoutActivity
from Modules.text_channels_control import add_game_in_game_roles_channel
from utils import get_bot, clean_channel_id, parse_time
from Modules.logger import extract_fields

bot = get_bot()


# Создание каналов для автоматического поиска компании
@bot.tree.command(name="create_party_search_channel", description="[admin] create channels for automatic party search.")
@app_commands.describe()
@app_commands.checks.has_permissions(administrator=True)
async def create_party_search_channel(interaction: discord.Interaction):
    guild = interaction.guild
    text_channel = await guild.create_text_channel('party-search-text')
    voice_channel = await guild.create_voice_channel('party-search-voice')

    text_channel_id = text_channel.id
    voice_channel_id = voice_channel.id
    guild_id = guild.id

    await write_to_guild_settings_db(guild_id, "party_find_text_channel_id", f"id{text_channel_id}")
    await write_to_guild_settings_db(guild_id, "party_find_voice_channel_id", f"id{voice_channel_id}")
    find_message_without_activity = await text_channel.send(await get_phrase('Create a party search', guild))
    await write_to_buttons_db(guild.id, find_message_without_activity.id, "FindPartyWithoutActivity", '{}', 12345)
    modal = FindPartyWithoutActivity(guild)
    await modal.add_buttons()
    await find_message_without_activity.edit(view=modal)

    await interaction.response.send_message(f"{await get_phrase('channels for party search created', guild)}:\n"
                                            f"{await get_phrase('Text Channel', guild)}: {text_channel.mention}\n"
                                            f"{await get_phrase('Voice Channel', guild)}: {voice_channel.mention}")


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
        await delete_from_guild_settings_db(interaction.guild.id, 'language')
        await write_to_guild_settings_db(interaction.guild.id, "language", lang)

        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        description = await get_phrase('language_changed', interaction.guild)
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
    top_games = await get_top_games(guild_id, days, granularity)
    top_games = top_games[:top]

    graph_buf = await plot_top_games(interaction.guild, top_games, days, granularity)

    embed = await top_games_create_embed(top_games, days, granularity, interaction.guild)

    file = discord.File(fp=graph_buf, filename="top_games.png")
    embed.set_image(url="attachment://top_games.png")
    await interaction.response.send_message(embed=embed, file=file)

# Получение графика популярности игры на сервере
@bot.tree.command(name="game_popularity_chart", description="Get game popularity chart for the last N days.")
@app_commands.describe(days="Number of days to analyze", granularity="Granularity (day, week, month)", game="Name of the game")

async def game_popularity_chart(interaction: discord.Interaction, days: int, granularity: str, game: str):

    graph_buf = await plot_top_games(interaction.guild, [], days, granularity, game)

    embed = await popularity_games_create_embed(game, days, granularity, interaction.guild)

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
        await interaction.response.send_message(await get_phrase('You need to specify the on/off mode'),
                                                ephemeral=True)
    else:
        try:
            await delete_from_guild_settings_db(interaction.guild.id, 'removing_greetings')
            await delete_from_guild_settings_db(interaction.guild.id, 'removing_greetings_delay')
        except:
            pass
        await write_to_guild_settings_db(interaction.guild.id, "removing_greetings", mode)
        await write_to_guild_settings_db(interaction.guild.id, "removing_greetings_delay", delay)

        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        if mode == 'on':

            description = (f"{await get_phrase('Automatic greeting deletion enabled', interaction.guild)}.\n"
                                                    f"{await get_phrase('Delay', interaction.guild)} {delay} "
                                                    f"{await get_phrase('seconds', interaction.guild)}.")
            embed.description = description
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        else:
            description = await get_phrase('Automatic greeting deletion disabled', interaction.guild)
            embed.description = description
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

async def check_and_assign_roles(guild, top_games):
    for game in top_games:
        game_name = game[0]
        role_name = game_name

        role = discord.utils.get(guild.roles, name=role_name)

        if role is None:
            random_color = random.randint(0, 0xFFFFFF)
            role = await guild.create_role(name=role_name, color=discord.Color(random_color))
            await add_game_in_game_roles_channel({role}, guild)

# Создание ролей для X популярных игр на сервере
@bot.tree.command(name="create_top_games_roles", description="[admin] create roles for top games.")
@app_commands.describe(top_count="Количество топ игр для создания ролей (например, топ 5)")
@app_commands.checks.has_permissions(administrator=True)
async def create_top_games_roles(interaction: discord.Interaction, top_count: int):
    await interaction.response.defer()

    guild = interaction.guild

    top_games = get_top_games(guild.id, 30, 'day')

    if not top_games:
        await interaction.followup.send("Нет данных о топ играх за указанный период.", ephemeral=True)
        return

    top_games = top_games[:top_count]

    try:
        await check_and_assign_roles(guild, top_games)

        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        description = await get_phrase('Roles for top games have been created', interaction.guild) % top_count
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
        await delete_member_data_from_db(interaction.user, 'voice_channel_name')
    except:
        pass
    await write_to_members_db(interaction.user, 'voice_channel_name', name)

    embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
    description = await get_phrase('Name_personal_voice_set', interaction.guild)
    embed.description = description

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )

@bot.tree.command(name="update_game_roles", description="[Global] Enable/disable game role update")
@app_commands.describe(mode="Mode (on, off)")
async def dont_update_roles(interaction: discord.Interaction, mode: str):
    try:
        await delete_member_data_from_db(interaction.user, 'game_roles_update')
    except:
        pass
    await write_to_members_db(interaction.user, 'game_roles_update', mode)

    embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
    if mode == 'on':
        description = await get_phrase('Game Roles Update Enabled', interaction.guild)
    else:
        description = await get_phrase('Game role Update disabled', interaction.guild)
    embed.description = description

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )

@bot.tree.command(name="logging_system", description="[admin] Toggle logging system.")
@app_commands.describe(mode="logging mode (on, off)")
@app_commands.checks.has_permissions(administrator=True)
async def logging_system(interaction: discord.Interaction, mode: str):
    if mode not in ['on', 'off']:
        await interaction.response.send_message("Invalid mode! Use 'on' or 'off'.", ephemeral=True)
        return

    guild = interaction.guild

    log_channel_ids = [clean_channel_id(id_str) for id_str in await read_from_guild_settings_db(guild.id, "log_channel_ids")]

    if not log_channel_ids:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),  # Запретить всем
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        log_channel = await guild.create_text_channel("log-channel", overwrites=overwrites)
        await write_to_guild_settings_db(guild.id, "log_channel_id", f"id{log_channel.id}")
        await interaction.response.send_message(f"Logging channel created: {log_channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("Logging channel already exists.", ephemeral=True)

    await write_to_guild_settings_db(guild.id, "logging_system", mode)

    await interaction.followup.send(f"Logging system has been turned {'on' if mode == 'on' else 'off'}.",
                                    ephemeral=True)

@bot.tree.command(name="set_utc_time", description="[admin] Set UTC time for the server.")
@app_commands.describe(utc_offset="UTC offset (e.g., 0, +11, -5)")
@app_commands.checks.has_permissions(administrator=True)
async def set_utc_time(interaction: discord.Interaction, utc_offset: int):
    guild = interaction.guild

    if utc_offset < -12 or utc_offset > 14:
        await interaction.response.send_message("Invalid UTC offset! Please provide a value between -12 and +14.", ephemeral=True)
        return

    await delete_from_guild_settings_db(guild.id, "utc_time_offset")

    await write_to_guild_settings_db(guild.id, "utc_time_offset", utc_offset)

    await interaction.response.send_message(f"UTC time offset set to {utc_offset}.", ephemeral=True)


def has_delete_messages_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True

    user_roles = interaction.user.roles
    for role in user_roles:
        if role.permissions.manage_messages:
            return True

    return False

@bot.tree.command(name="get_logs", description="[admin] Get logs from the analytics database.")
@app_commands.describe(event_type="Type of event to filter", start_time="Start time for the logs",
                       end_time="End time for the logs", search_str="Search terms in data",
                       operator="Search operator: AND or OR")
@app_commands.check(has_delete_messages_permission)
async def get_logs(interaction: discord.Interaction, event_type: str = None, start_time: str = None,
                   end_time: str = None, search_str: str = None, operator: str = 'AND'):
    ephemeral_response = await interaction.response.send_message("Loading...", ephemeral=True)
    guild_id = interaction.guild.id
    start_time_str = start_time
    end_time_str = end_time
    logging_status = await read_from_guild_settings_db(guild_id, "logging_system")
    if not (logging_status and logging_status[0] == 'on'):
        await interaction.edit_original_response(content = "Logging system is turned off.")
        #await interaction.response.send_message("Logging system is turned off.", ephemeral=True)
        return
    utc_offset_data = await read_from_guild_settings_db(guild_id, "utc_time_offset")
    utc_offset = int(utc_offset_data[0]) if utc_offset_data else 0

    start_time = parse_time(start_time, default_days_ago=365)
    end_time = parse_time(end_time, default_days_ago=0)

    logs = await read_logs_from_analytics(
        guild_id=guild_id,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        search_str=search_str,
        operator=operator
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    if not logs:
        await interaction.edit_original_response(
            content=f"{await get_phrase('No logs found for the specified filters', interaction.guild)}.\n"
                    f"{await get_phrase('start time', interaction.guild)} {start_time + timedelta(hours=utc_offset):{date_format}}\n"
                    f"{await get_phrase('input', interaction.guild)}: {start_time_str}\n"
                    f"{await get_phrase('end time', interaction.guild)} {end_time + timedelta(hours=utc_offset):{date_format}}\n"
                    f"{await get_phrase('input', interaction.guild)}: {end_time_str}\n"
                    f"{await get_phrase('search', interaction.guild)} {search_str}"
        )
        return

    await interaction.edit_original_response(content="Loading...")

    initial_message = await interaction.channel.send(f"{await get_phrase('Fetching logs', interaction.guild)}. "
                                                     f"{await get_phrase('Vars', interaction.guild)}:\n"
                                                     f"{await get_phrase('event type', interaction.guild)} {event_type}\n"
                                                     f"{await get_phrase('start time', interaction.guild)} {start_time + timedelta(hours=utc_offset):{date_format}}\n"
                                                     f"{await get_phrase('input', interaction.guild)}: {start_time_str}\n"
                                                     f"{await get_phrase('end time', interaction.guild)} {end_time + timedelta(hours=utc_offset):{date_format}}\n"
                                                     f"{await get_phrase('input', interaction.guild)}: {end_time_str}\n"
                                                     f"{await get_phrase('search', interaction.guild)} {search_str}\n"
                                                     f"{await get_phrase('operator', interaction.guild)} {operator}\n")

    thread = await initial_message.create_thread(name="Logs Thread", auto_archive_duration=60)

    def decode_misencoded_string(input_string: str) -> str:
        try:
            return input_string.encode('latin1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return input_string

    for log in sorted(logs, key=lambda x: x['date_time']):
        log_time = datetime.fromisoformat(log["date_time"]) + timedelta(hours=utc_offset)
        formatted_time = log_time.strftime("%Y-%m-%d %H:%M:%S")
        readable_data = await extract_fields(log['data'], log['event_type'], interaction.guild)

        description = (
            f"**{await get_phrase('Event Type', interaction.guild)}**: {log['event_type']}\n"
            f"**{await get_phrase('Logged At', interaction.guild)}**: {formatted_time}\n"
            f"**{await get_phrase('Data', interaction.guild)}**:\n{readable_data}\n"
        )
        embed = discord.Embed(description=description, color=discord.Color.from_str("#EE82EE"))
        await thread.send(embed=embed)

    await interaction.edit_original_response(content="Done.")

@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(await get_phrase('Command error', interaction.guild), ephemeral=True)