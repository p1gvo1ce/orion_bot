import discord
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import io
import os
from datetime import datetime, timedelta, timezone

# Подготовка данных о топ играх и построение графика
def plot_top_games(guild_id, guild_name, top_games, days, granularity, game = None):
    conn = sqlite3.connect(os.path.join("DataBase", "game_activities.db"))
    c = conn.cursor()
    table_name = f"guild_{guild_id}"
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

    # Определяем формат для гранулярности
    if granularity == 'day':
        date_format = '%Y-%m-%d'
        interval = '1 day'
    elif granularity == 'week':
        date_format = '%Y-%W'
        interval = '7 days'
    else:  # granularity == 'month'
        date_format = '%Y-%m'
        interval = '1 month'

    # Данные для графика
    if game:
        top_games = [[game]]
    game_data = {}
    for game in top_games:
        game_name = game[0]
        query = f"""
            SELECT strftime('{date_format}', datetime) as period, COUNT(DISTINCT member_id) as unique_players
            FROM {table_name}
            WHERE activity_name = ? AND datetime BETWEEN ? AND ?
            GROUP BY period
            ORDER BY period;
        """
        c.execute(query, (game_name, start_date_str, end_date_str))
        periods = c.fetchall()

        game_data[game_name] = periods
    conn.close()

    # Построение графика
    plt.figure(figsize=(10, 6))
    for game_name, periods in game_data.items():
        if periods:  # Проверяем, есть ли данные
            dates = [datetime.strptime(p[0], date_format) for p in periods]
            counts = [p[1] for p in periods]
            plt.plot(dates, counts, label=game_name)

    plt.xlabel(f'Time ({granularity})')
    plt.ylabel('Number of unique players')
    plt.title(f'Top games activity on {guild_name}')
    plt.legend()

    # Ограничение количества меток на оси X
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())  # Автоматический выбор интервалов
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Форматирование дат

    # Ограничение максимального количества меток на оси X
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=8))  # Максимум 8 меток

    # Установка границ графика
    plt.xlim([start_date, end_date])

    # Сохраняем график в байтовый буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return buf

# Функция для создания embed
def top_games_create_embed(top_games, days, granularity):
    embed = discord.Embed(title=f"Top {len(top_games)} Games Activity", color=discord.Color.blue())
    description = f"Data for the last {days} days with granularity: {granularity}\n\n"
    for i, game in enumerate(top_games):
        description += f"**{i+1}. {game[0]}** - {game[1]} unique players\n"
    embed.description = description
    return embed

# Функция для создания embed
def popularity_games_create_embed(game, days, granularity):
    embed = discord.Embed(title=f"{game} Activity", color=discord.Color.blue())
    description = f"{game} popularity chart for the last {days} days with granularity: {granularity}\n\n"
    embed.description = description
    return embed