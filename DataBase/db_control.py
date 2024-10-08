import os
import sqlite3

def check_and_initialize_db():



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