import discord
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import io
import os
from datetime import datetime, timedelta, timezone
from Modules.phrases import get_phrase

# Подготовка данных о топ играх и построение графика
def plot_top_games(guild, top_games, days, granularity, game = None):
    conn = sqlite3.connect(os.path.join("Data", "game_activities.db"))
    c = conn.cursor()
    guild_id = guild.id
    guild_name = guild.name
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

    plt.xlabel(f'{get_phrase('Time', guild)} ({granularity})')
    plt.ylabel(get_phrase('Number of unique players', guild))
    plt.title(f'{get_phrase('Top games activity on', guild)} {guild_name}')
    plt.legend()

    # Ограничение количества меток на оси X
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())  # Автоматический выбор интервалов
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Форматирование дат

    # Ограничение максимального количества меток на оси X
    if days > 8:
        plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=8))  # Максимум 8 меток
    else:
        plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=days))

    # Установка границ графика
    plt.xlim([start_date, end_date])

    # Сохраняем график в байтовый буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return buf

# Функция для создания embed
def top_games_create_embed(top_games, days, granularity, guild):
    conn = sqlite3.connect(os.path.join("Data", "game_activities.db"))
    c = conn.cursor()

    guild_id = guild.id
    table_name = f"guild_{guild_id}"

    # Запрос на получение общего количества уникальных пользователей за всё время
    query_total_unique_players = f"""
        SELECT COUNT(DISTINCT member_id) 
        FROM {table_name}
    """
    c.execute(query_total_unique_players)
    total_unique_players = c.fetchone()[0]
    conn.close()

    # Создание embed с основной информацией
    embed = discord.Embed(title=f"{get_phrase('Top', guild)} {len(top_games)} "
                                f"{get_phrase('Games Activity', guild)}", color=discord.Color.blue())
    description = (f"{get_phrase('Data for the last', guild)} {days} "
                   f"{get_phrase('days with granularity', guild)}: {granularity}\n\n")
    for i, game in enumerate(top_games):
        description += f"**{i + 1}. {game[0]}** - {game[1]} {get_phrase('unique players', guild)}\n"
    embed.description = description

    # Добавление информации в подвал
    embed.set_footer(text=f"{get_phrase('Data based on', guild)} {total_unique_players} "
                          f"{get_phrase('unique players over all time', guild)}")

    return embed

def popularity_games_create_embed(game, days, granularity, guild):
    conn = sqlite3.connect(os.path.join("Data", "game_activities.db"))
    c = conn.cursor()

    guild_id = guild.id
    table_name = f"guild_{guild_id}"

    # Запрос на получение общего количества уникальных пользователей за всё время
    query_total_unique_players = f"""
        SELECT COUNT(DISTINCT member_id) 
        FROM {table_name}
    """
    c.execute(query_total_unique_players)
    total_unique_players = c.fetchone()[0]
    conn.close()

    # Создание embed с основной информацией
    embed = discord.Embed(title=f"{game} Activity", color=discord.Color.blue())
    description = (f"{game} {get_phrase('popularity chart for the last', guild)} {days} "
                   f"{get_phrase('days with granularity', guild)}: {granularity}\n\n")
    embed.description = description

    # Добавление информации в подвал
    embed.set_footer(text=f"{get_phrase('Data based on', guild)} {total_unique_players} "
                          f"{get_phrase('unique players over all time', guild)}")

    return embed
