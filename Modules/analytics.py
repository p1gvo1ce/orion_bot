import discord
import aiosqlite
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import io
import os
from datetime import datetime, timedelta, timezone
from Modules.phrases import get_phrase

async def plot_top_games(guild, top_games, days, granularity, game=None):
    db_path = os.path.join("Data", "game_activities.db")
    guild_id = guild.id
    guild_name = guild.name
    table_name = f"guild_{guild_id}"
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

    if granularity == 'day':
        date_format = '%Y-%m-%d'
        interval = '1 day'
    elif granularity == 'week':
        date_format = '%Y-%W'
        interval = '7 days'
    else:  # granularity == 'month'
        date_format = '%Y-%m'
        interval = '1 month'

    if game:
        top_games = [[game]]
    game_data = {}

    async with aiosqlite.connect(db_path) as conn:
        for game in top_games:
            game_name = game[0]
            query = f"""
                SELECT strftime('{date_format}', datetime) as period, COUNT(DISTINCT member_id) as unique_players
                FROM {table_name}
                WHERE activity_name = ? AND datetime BETWEEN ? AND ?
                GROUP BY period
                ORDER BY period;
            """
            async with conn.execute(query, (game_name, start_date_str, end_date_str)) as cursor:
                periods = await cursor.fetchall()
                game_data[game_name] = periods

    plt.figure(figsize=(10, 6))
    for game_name, periods in game_data.items():
        if periods:
            dates = [datetime.strptime(p[0], date_format) for p in periods]
            counts = [p[1] for p in periods]
            plt.plot(dates, counts, label=game_name)

    plt.xlabel(f'{await get_phrase("Time", guild)} ({granularity})')
    plt.ylabel(await get_phrase('Number of unique players', guild))
    plt.title(f'{await get_phrase("Top games activity on", guild)} {guild_name}')
    plt.legend()

    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    if days > 8:
        plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=8))
    else:
        plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=days))

    plt.xlim([start_date, end_date])

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return buf


async def top_games_create_embed(top_games, days, granularity, guild):
    db_path = os.path.join("Data", "game_activities.db")
    guild_id = guild.id
    table_name = f"guild_{guild_id}"

    async with aiosqlite.connect(db_path) as conn:
        query_total_unique_players = f"""
            SELECT COUNT(DISTINCT member_id) 
            FROM {table_name}
        """
        async with conn.execute(query_total_unique_players) as cursor:
            total_unique_players = await cursor.fetchone()
            total_unique_players = total_unique_players[0] if total_unique_players else 0

    embed = discord.Embed(
        title=f"{await get_phrase('Top', guild)} {len(top_games)} {await get_phrase('Games Activity', guild)}",
        color=discord.Color.blue()
    )

    description = (f"{await get_phrase('Data for the last', guild)} {days} "
                   f"{await get_phrase('days with granularity', guild)}: {granularity}\n\n")

    for i, game in enumerate(top_games):
        description += f"**{i + 1}. {game[0]}** - {game[1]} {await get_phrase('unique players', guild)}\n"

    embed.description = description

    embed.set_footer(text=f"{await get_phrase('Data based on', guild)} {total_unique_players} "
                          f"{await get_phrase('unique players over all time', guild)}")

    return embed

async def popularity_games_create_embed(game, days, granularity, guild):
    db_path = os.path.join("Data", "game_activities.db")
    guild_id = guild.id
    table_name = f"guild_{guild_id}"

    async with aiosqlite.connect(db_path) as conn:
        query_total_unique_players = f"""
            SELECT COUNT(DISTINCT member_id) 
            FROM {table_name}
        """
        async with conn.execute(query_total_unique_players) as cursor:
            total_unique_players = await cursor.fetchone()
            total_unique_players = total_unique_players[0] if total_unique_players else 0

    embed = discord.Embed(title=f"{game} Activity", color=discord.Color.blue())
    description = (f"{game} {await get_phrase('popularity chart for the last', guild)} {days} "
                   f"{await get_phrase('days with granularity', guild)}: {granularity}\n\n")
    embed.description = description

    embed.set_footer(text=f"{await get_phrase('Data based on', guild)} {total_unique_players} "
                          f"{await get_phrase('unique players over all time', guild)}")

    return embed