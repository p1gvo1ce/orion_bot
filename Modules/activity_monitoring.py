import discord
import json
import asyncio
import os
from datetime import datetime
from Modules.db_control import check_and_initialize_activities_db, create_server_table, insert_activity
from utils import get_logger, logger

logger = get_logger()
JSON_DIR = 'Modules/jsons'

def ensure_json_directory_exists():
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
        print(f"Directory {JSON_DIR} created.")

def get_activity_file_path(guild_id):
    return os.path.join(JSON_DIR, f'last_activities_{guild_id}.json')

def save_activity_data(guild_id, activity_data):
    ensure_json_directory_exists()
    activity_file = get_activity_file_path(guild_id)
    with open(activity_file, 'w') as file:
        json.dump(activity_data, file, indent=4)

async def check_all_members(guild, db_conn):
    activity_data = {}
    roles = guild.roles

    for member in guild.members:
        if member.activity and member.activity.type == discord.ActivityType.playing:
            activity_name = member.activity.name
            member_id = str(member.id)

            activity_data[member_id] = {
                'id': member_id,
                'activities': [{
                    'activity_name': activity_name,
                    'timestamp': str(discord.utils.utcnow())
                }]
            }

            insert_activity(db_conn, guild.id, member_id, activity_name)

            role = discord.utils.get(roles, name=activity_name)
            if role:
                if role not in member.roles:
                    await member.add_roles(role)

    save_activity_data(guild.id, activity_data)


async def periodic_check_for_guilds(bot):
    db_conn = check_and_initialize_activities_db()
    while True:
        server_names = []
        for guild in bot.guilds:
            create_server_table(db_conn, guild.id)
            await check_all_members(guild, db_conn)
            server_names.append(guild.name)
        current_time = datetime.now().strftime('%Y.%m.%d %H.%M')
        logger.info(f"[{current_time}] Activity data updated for servers: " + ", ".join(server_names))
        await asyncio.sleep(600)