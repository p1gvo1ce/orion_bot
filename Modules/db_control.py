import os
import sqlite3
import aiosqlite
import asyncio
import json
from datetime import datetime, timedelta, timezone


async def check_and_initialize_main_db():
    db_path = os.path.join("Data", "main.db")

    if not os.path.exists(db_path):
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute('''CREATE TABLE tokens (id INTEGER PRIMARY KEY, token TEXT)''')
            await conn.commit()
    else:
        conn = await aiosqlite.connect(db_path)

    return conn


async def get_token_from_db(conn):
    async with conn.execute("SELECT token FROM tokens ORDER BY id DESC LIMIT 1") as cursor:
        result = await cursor.fetchone()
        if result:
            return result[0]
        else:
            return None


async def update_token_in_db(conn, token):
    await conn.execute("INSERT INTO tokens (token) VALUES (?)", (token,))
    await conn.commit()


async def request_token(conn):
    while True:
        token = input("Enter token: ").strip()
        if token:
            await update_token_in_db(conn, token)
            print("Token saved")
            return token


async def check_and_initialize_activities_db():
    db_path = os.path.join("Data", "game_activities.db")
    if not os.path.exists(db_path):
        async with aiosqlite.connect(db_path) as conn:
            pass
    else:
        conn = await aiosqlite.connect(db_path)

    return conn

async def create_server_table(conn, guild_id):
    table_name = f"guild_{guild_id}"
    async with conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            datetime DATETIME, 
            member_id TEXT, 
            activity_name TEXT
        )
    """):
        await conn.commit()

async def insert_activity(conn, guild_id, member_id, activity_name):
    table_name = f"guild_{guild_id}"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefixed_member_id = f"id_{member_id}"
    await conn.execute(f"""
        INSERT INTO {table_name} (datetime, member_id, activity_name) 
        VALUES (?, ?, ?)
    """, (current_time, prefixed_member_id, activity_name))
    await conn.commit()

async def close_connection(conn):
    await conn.close()

async def get_recent_activity_members(guild_id, activity_name, minutes=10):
    db_path = os.path.join("Data", "game_activities.db")
    conn = await aiosqlite.connect(db_path)
    table_name = f"guild_{guild_id}"
    time_threshold = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")

    async with conn.execute(f"""
        SELECT DISTINCT member_id 
        FROM {table_name}
        WHERE activity_name = ? AND datetime >= ?
    """, (activity_name, time_threshold)) as cursor:
        results = await cursor.fetchall()

    await conn.close()
    return [row[0].replace("id_", "") for row in results]

async def get_top_games(guild_id, days, granularity):
    db_path = os.path.join("Data", "game_activities.db")
    table_name = f"guild_{guild_id}"
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Формат даты для SQLite
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

    query = f"""
        SELECT activity_name, COUNT(DISTINCT member_id)
        FROM {table_name}
        WHERE datetime BETWEEN ? AND ?
        GROUP BY activity_name
        ORDER BY COUNT(DISTINCT member_id) DESC
        LIMIT 10;
    """

    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(query, (start_date_str, end_date_str)) as cursor:
            result = await cursor.fetchall()

    return result

async def create_guild_table(guild_id):
    db_path = os.path.join("Data", "main.db")
    table_name = f"guild_{guild_id}"

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                param_name TEXT PRIMARY KEY,
                param_value TEXT
            )
        """)
        await conn.commit()


async def write_to_guild_settings_db(guild_id, param_name, param_value):
    db_path = os.path.join("Data", "main.db")
    await create_guild_table(guild_id)  # Предполагаем, что эта функция тоже будет асинхронной

    async with aiosqlite.connect(db_path) as conn:
        table_name = f"guild_{guild_id}"
        await conn.execute(f"""
            INSERT INTO {table_name} (param_name, param_value)
            VALUES (?, ?)
            ON CONFLICT(param_name) DO UPDATE SET param_value = excluded.param_value
        """, (param_name, param_value))
        await conn.commit()

async def delete_from_guild_settings_db(guild_id: int, param_name: str) -> None:
    db_path = os.path.join("Data", "main.db")
    async with aiosqlite.connect(db_path) as conn:
        table_name = f"guild_{guild_id}"
        await conn.execute(f"DELETE FROM {table_name} WHERE param_name = ?", (param_name,))
        await conn.commit()


async def read_from_guild_settings_db(guild_id, param_name):
    db_path = os.path.join("Data", "main.db")
    table_name = f"guild_{guild_id}"

    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(f"SELECT param_value FROM {table_name} WHERE param_name = ?", (param_name,)) as cursor:
            results = await cursor.fetchall()

    return [result[0] for result in results] if results else []

async def create_buttons_table():
    db_path = os.path.join("Data", "main.db")

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS buttons (
                server_id INTEGER,
                message_id INTEGER PRIMARY KEY,
                button_type TEXT,
                data TEXT,
                member_id INTEGER
            )
        """)
        await conn.commit()

async def write_to_buttons_db(server_id, message_id, button_type, data=None, member_id=None):
    db_path = os.path.join("Data", "main.db")
    await create_buttons_table()

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            INSERT INTO buttons (server_id, message_id, button_type, data, member_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(message_id) DO UPDATE SET button_type = excluded.button_type, data = excluded.data, member_id = excluded.member_id
        """, (server_id, message_id, button_type, json.dumps(data), member_id))
        await conn.commit()

async def read_button_data_from_db(message_id):
    db_path = os.path.join("Data", "main.db")
    await create_buttons_table()

    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute("SELECT server_id, button_type, data, member_id FROM buttons WHERE message_id = ?", (message_id,)) as cursor:
            result = await cursor.fetchone()

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

async def delete_button_data_from_db(message_id):
    db_path = os.path.join("Data", "main.db")
    await create_buttons_table()

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("DELETE FROM buttons WHERE message_id = ?", (message_id,))
        await conn.commit()

async def read_all_buttons_data():
    db_path = os.path.join("Data", "main.db")
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute("SELECT message_id, server_id, button_type, data, member_id FROM buttons") as cursor:
            results = await cursor.fetchall()

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

async def check_and_initialize_members_db():
    db_path = os.path.join("Data", "members.db")
    if not os.path.exists(db_path):
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute('''CREATE TABLE settings (member_id INTEGER PRIMARY KEY, option TEXT, data TEXT)''')
            await conn.commit()
        return None
    else:
        return await aiosqlite.connect(db_path)


async def create_settings_table():
    await check_and_initialize_members_db()
    db_path = os.path.join("Data", "members.db")

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                member_id INTEGER PRIMARY KEY,
                option TEXT,
                data TEXT
            )
        """)
        await conn.commit()


async def write_to_members_db(member, option, data=None):
    db_path = os.path.join("Data", "members.db")
    await create_settings_table()

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            INSERT INTO settings (member_id, option, data)
            VALUES (?, ?, ?)
            ON CONFLICT(member_id) DO UPDATE SET option = excluded.option, data = excluded.data
        """, (member.id, option, json.dumps(data)))
        await conn.commit()


async def read_member_data_from_db(member, option):
    db_path = os.path.join("Data", "members.db")
    await create_settings_table()

    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute("SELECT data FROM settings WHERE member_id = ? AND option = ?",
                                (member.id, option)) as cursor:
            result = await cursor.fetchone()

    if result:
        data_json = result[0]
        data = json.loads(data_json)
        return {
            "member_id": member.id,
            "option": option,
            "data": data
        }
    return None

async def delete_member_data_from_db(member, option):
    db_path = os.path.join("Data", "members.db")
    await create_settings_table()

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("DELETE FROM settings WHERE member_id = ? AND option = ?", (member.id, option))
        await conn.commit()


async def check_and_initialize_logs_db(guild_id, db_type="buffer"):
    if db_type == "buffer":
        db_path = os.path.join("Data", "logs.db")
    elif db_type == "analytics":
        db_path = os.path.join("Data", "analytics.db")  # Указанный путь для аналитической БД
    else:
        raise ValueError("Неверный тип базы данных. Используйте 'buffer' или 'analytics'.")
    if not os.path.exists("Data"):
        os.makedirs("Data")  # Создаем папку, если её нет

    conn = await aiosqlite.connect(db_path)

    table_name = f"guild{guild_id}"
    await conn.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT,
            event_type TEXT,
            data TEXT
        )
    ''')

    return conn


async def log_event_to_db(guild_id, event_type, data):
    db_path = os.path.join("Data", "logs.db")
    async with aiosqlite.connect(db_path) as conn:
        data_json = json.dumps(data, ensure_ascii=False)
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        table_name = f"guild{guild_id}"
        await conn.execute(f'''
            INSERT INTO {table_name} (date_time, event_type, data)
            VALUES (?, ?, ?)
        ''', (current_time, event_type, data_json))

        await conn.commit()


async def copy_logs_to_analytics(guild_id):
    buffer_db_path = os.path.join("Data", "logs.db")
    analytics_db_path = os.path.join("Data", "analytics.db")

    async with aiosqlite.connect(buffer_db_path) as buffer_conn, \
            aiosqlite.connect(analytics_db_path) as analytics_conn:
        table_name = f"guild{guild_id}"

        async with buffer_conn.execute(f"SELECT date_time, event_type, data FROM {table_name}") as buffer_cursor:
            logs_to_copy = await buffer_cursor.fetchall()

        if logs_to_copy:
            await analytics_conn.executemany(f'''
                INSERT INTO {table_name} (date_time, event_type, data)
                VALUES (?, ?, ?)
            ''', logs_to_copy)

            await buffer_conn.execute(f"DELETE FROM {table_name}")

        await buffer_conn.commit()
        await analytics_conn.commit()




async def read_logs_from_analytics(guild_id, event_type=None, start_time=None, end_time=None, search_str=None, operator='AND'):
    analytics_db_path = os.path.join("Data", "analytics.db")

    async with aiosqlite.connect(analytics_db_path) as conn:
        table_name = f"guild{guild_id}"
        query = f"SELECT date_time, event_type, data FROM {table_name} WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if start_time:
            query += " AND date_time >= ?"
            params.append(start_time)

        if end_time:
            query += " AND date_time <= ?"
            params.append(end_time)

        if search_str:
            search_terms = [term.strip().lower() for term in search_str.split(',')]
            if operator.upper() == 'AND':
                like_conditions = " AND ".join([f"LOWER(data) LIKE ?" for _ in search_terms])
            else:
                like_conditions = " OR ".join([f"LOWER(data) LIKE ?" for _ in search_terms])

            query += f" AND ({like_conditions})"
            params.extend([f"%{term}%" for term in search_terms])

        async with conn.execute(query, params) as cursor:
            logs = await cursor.fetchall()

    if not logs:
        print("Нет логов для указанных параметров:")
        print(f"start_time: {start_time}, end_time: {end_time}, event_type: {event_type}, search_str: {search_str}")

    parsed_logs = []
    for log in logs:
        date_time, event_type, data = log
        try:
            decoded_data = decode_misencoded_string(data)
            json_data = decoded_data

            parsed_logs.append({
                "date_time": date_time,
                "event_type": event_type,
                "data": json_data
            })
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON для данных: {data}")
            print(f"Ошибка: {e}")

    return parsed_logs



def decode_misencoded_string(input_string: str) -> str:
    try:
        return input_string.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return input_string

async def copy_logs_to_analytics(guilds):
    buffer_db_path = os.path.join("Data", "logs.db")
    analytics_db_path = os.path.join("Data", "analytics.db")
    while True:
        for guild in guilds:
            guild_id = guild.id
            try:
                await check_and_initialize_logs_db(guild_id, db_type="analytics")
                await check_and_initialize_logs_db(guild_id, db_type="buffer")
                async with aiosqlite.connect(buffer_db_path) as buffer_conn, aiosqlite.connect(
                        analytics_db_path) as analytics_conn:
                    async with buffer_conn.cursor() as buffer_cursor, analytics_conn.cursor() as analytics_cursor:

                        table_name = f"guild{guild_id}"
                        await buffer_cursor.execute(f"SELECT date_time, event_type, data FROM {table_name}")
                        logs_to_copy = await buffer_cursor.fetchall()

                        if logs_to_copy:
                            await analytics_cursor.executemany(f'''
                                INSERT INTO {table_name} (date_time, event_type, data)
                                VALUES (?, ?, ?)
                            ''', logs_to_copy)

                            await buffer_cursor.execute(f"DELETE FROM {table_name}")

                        await buffer_conn.commit()
                        await analytics_conn.commit()

            except Exception as e:
                print(f"Error copying logs to analytics: {e}")

            print('DB COPIED')
        await asyncio.sleep(300)  # Ждем 10 минут
