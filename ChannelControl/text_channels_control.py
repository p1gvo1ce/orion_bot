from utils import clean_channel_id
from DataBase.db_control import read_from_guild_settings_db, write_to_guild_settings_db


async def ensure_game_roles_channel(guild):
    game_roles_channel_ids = read_from_guild_settings_db(guild.id, "game_roles_channel_id")

    game_roles_channel_ids = [clean_channel_id(id_str) for id_str in game_roles_channel_ids]

    if not game_roles_channel_ids:
        game_roles_channel = await guild.create_text_channel("game-roles")
        write_to_guild_settings_db(guild.id, "game_roles_channel_id", f"id{game_roles_channel.id}")
    else:
        game_roles_channel = guild.get_channel(int(game_roles_channel_ids[0].replace("id", "")))

    return game_roles_channel

async def add_game_in_game_roles_channel(role, guild):
    game_roles_channel = await ensure_game_roles_channel(guild)

    message = await game_roles_channel.send(f"{role.mention} создана!")
    await message.add_reaction("🎮")
