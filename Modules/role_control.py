from utils import clean_channel_id, get_bot
from Modules.db_control import read_from_guild_settings_db


async def game_role_reaction_add(payload):
    bot = get_bot()
    user = payload.member
    if payload.member.bot:
        return

    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    guild_id = message.guild.id
    game_roles_channel_ids = read_from_guild_settings_db(guild_id, "game_roles_channel_id")

    game_roles_channel_ids = [clean_channel_id(id_str) for id_str in game_roles_channel_ids]

    if channel.id in game_roles_channel_ids:
        role_mentions = message.role_mentions
        if role_mentions:
            role = role_mentions[0]
            if role not in user.roles:
                await user.add_roles(role)


async def game_role_reaction_remove(payload):
    bot = get_bot()

    guild = bot.get_guild(payload.guild_id)

    member = await guild.fetch_member(payload.user_id)

    if member.bot:
        return

    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    guild_id = message.guild.id
    game_roles_channel_ids = read_from_guild_settings_db(guild_id, "game_roles_channel_id")

    game_roles_channel_ids = [clean_channel_id(id_str) for id_str in game_roles_channel_ids]

    if channel.id in game_roles_channel_ids:
        role_mentions = message.role_mentions
        if role_mentions:
            role = role_mentions[0]
            if role in member.roles:
                await member.remove_roles(role)