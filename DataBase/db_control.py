import os
import sqlite3
import datetime

def check_and_initialize_main_db():



    # Проверка наличия базы данных main.db
    db_path = os.path.join("DataBase", "main.db")
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE tokens (id INTEGER PRIMARY KEY, token TEXT)''')
        conn.commit()
        print("Создана база данных 'main.db' и таблица 'tokens'.")
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
        token = input("Введите токен для подключения: ").strip()
        if token:
            update_token_in_db(conn, token)
            print("Токен сохранен.")
            return token


def check_and_initialize_activities_db():
    # Проверка наличия базы данных game_activities.db
    db_path = os.path.join("DataBase", "game_activities.db")
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        print("Создана база данных 'game_activities.db'.")
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
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefixed_member_id = f"id_{member_id}"
    c.execute(f"INSERT INTO {table_name} (datetime, member_id, activity_name) VALUES (?, ?, ?)",
              (current_time, prefixed_member_id, activity_name))
    conn.commit()
def close_connection(conn):
    conn.close()