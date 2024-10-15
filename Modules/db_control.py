import os
import sqlite3
import json
from datetime import datetime, timedelta, timezone

def check_and_initialize_main_db():
    db_path = os.path.join("Data", "main.db")
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE tokens (id INTEGER PRIMARY KEY, token TEXT)''')
        conn.commit()
    else:
        conn = sqlite3.connect(db_path)
    return conn


def get_token_from_db(conn):
    c = conn.cursor()
    c.execute("SELECT token FROM tokens ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    if result:
        return result[0]
    else:
        return None


def update_token_in_db(conn, token):
    c = conn.cursor()
    c.execute("INSERT INTO tokens (token) VALUES (?)", (token,))
    conn.commit()


def request_token(conn):
    while True:
        token = input("Введите токен / Enter token: ").strip()
        if token:
            update_token_in_db(conn, token)
            print("Токен сохранен.\nToken saved")
            return token


def check_and_initialize_activities_db():
    db_path = os.path.join("Data", "game_activities.db")
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
    else:
        conn = sqlite3.connect(db_path)

    return conn

def create_server_table(conn, guild_id):
    c = conn.cursor()
    table_name = f"guild_{guild_id}"
    c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (datetime DATETIME, member_id TEXT, activity_name TEXT)")
    conn.commit()

def insert_activity(conn, guild_id, member_id, activity_name):
    c = conn.cursor()
    table_name = f"guild_{guild_id}"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefixed_member_id = f"id_{member_id}"
    c.execute(f"INSERT INTO {table_name} (datetime, member_id, activity_name) VALUES (?, ?, ?)",
              (current_time, prefixed_member_id, activity_name))
    conn.commit()
def close_connection(conn):
    conn.close()

# Получение ids по активности за последние 10 минут
def get_recent_activity_members(guild_id, activity_name, minutes=10):
    conn = sqlite3.connect(os.path.join("Data", "game_activities.db"))
    c = conn.cursor()
    table_name = f"guild_{guild_id}"
    time_threshold = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")

    c.execute(f"""
        SELECT DISTINCT member_id 
        FROM {table_name}
        WHERE activity_name = ? AND datetime >= ?
    """, (activity_name, time_threshold))

    results = c.fetchall()
    conn.close()
    return [row[0].replace("id_", "") for row in results]  # Убираем префикс "id_"


# Функция для получения данных из базы данных
def get_top_games(guild_id, days, granularity):
    conn = sqlite3.connect(os.path.join("Data", "game_activities.db"))
    c = conn.cursor()

    table_name = f"guild_{guild_id}"
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Формат даты для SQLite
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

    # Запрос для получения активности за последние N дней
    query = f"""
        SELECT activity_name, COUNT(DISTINCT member_id)
        FROM {table_name}
        WHERE datetime BETWEEN ? AND ?
        GROUP BY activity_name
        ORDER BY COUNT(DISTINCT member_id) DESC
        LIMIT 10;
    """
    c.execute(query, (start_date_str, end_date_str))
    result = c.fetchall()
    conn.close()

    return result

# Создание таблицы с настройками сервера в main.db
def create_guild_table(guild_id):
    db_path = os.path.join("Data", "main.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    table_name = f"guild_{guild_id}"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            param_name TEXT PRIMARY KEY,
            param_value TEXT
        )
    """)

    conn.commit()
    conn.close()


# Запись данных в таблицу сервера
def write_to_guild_settings_db(guild_id, param_name, param_value):
    db_path = os.path.join("Data", "main.db")
    create_guild_table(guild_id)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    table_name = f"guild_{guild_id}"

    cursor.execute(f"""
        INSERT INTO {table_name} (param_name, param_value)
        VALUES (?, ?)
        ON CONFLICT(param_name) DO UPDATE SET param_value = excluded.param_value
    """, (param_name, param_value))

    conn.commit()
    conn.close()

# Удаление данных из таблицы сервера
def delete_from_guild_settings_db(guild_id: int, param_name: str) -> None:
    db_path = os.path.join("Data", "main.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    table_name = f"guild_{guild_id}"

    # Удаляем параметр
    cursor.execute(f"DELETE FROM {table_name} WHERE param_name = ?", (param_name,))

    conn.commit()
    conn.close()


# Чтение данных из таблицы сервера
def read_from_guild_settings_db(guild_id, param_name):
    db_path = os.path.join("Data", "main.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    table_name = f"guild_{guild_id}"

    cursor.execute(f"SELECT param_value FROM {table_name} WHERE param_name = ?", (param_name,))
    results = cursor.fetchall()

    conn.close()

    return [result[0] for result in results] if results else []

def create_buttons_table():
    db_path = os.path.join("Data", "main.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buttons (
            server_id INTEGER,
            message_id INTEGER PRIMARY KEY,
            button_type TEXT,
            data TEXT,
            member_id INTEGER
        )
    """)

    conn.commit()
    conn.close()

def write_to_buttons_db(server_id, message_id, button_type, data=None, member_id=None):
    db_path = os.path.join("Data", "main.db")
    create_buttons_table()  # Убедимся, что таблица создана

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO buttons (server_id, message_id, button_type, data, member_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET button_type = excluded.button_type, data = excluded.data, member_id = excluded.member_id
    """, (server_id, message_id, button_type, json.dumps(data), member_id))

    conn.commit()
    conn.close()

def read_button_data_from_db(message_id):
    db_path = os.path.join("Data", "main.db")
    create_buttons_table()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT server_id, button_type, data, member_id FROM buttons WHERE message_id = ?", (message_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        server_id, button_type, data_json, member_id = result
        data = json.loads(data_json)
        return {
            "server_id": server_id,
            "button_type": button_type,
            "data": data,
            "member_id": member_id
        }
    return None

def delete_button_data_from_db(message_id):
    db_path = os.path.join("Data", "main.db")
    create_buttons_table()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM buttons WHERE message_id = ?", (message_id,))
    conn.commit()
    conn.close()

def read_all_buttons_data():
    db_path = os.path.join("Data", "main.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT message_id, server_id, button_type, data, member_id FROM buttons")
    results = cursor.fetchall()

    conn.close()

    return [
        {
            "message_id": row[0],
            "server_id": row[1],
            "button_type": row[2],
            "data": json.loads(row[3]),
            "member_id": row[4]
        }
        for row in results
    ]