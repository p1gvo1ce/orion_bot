import discord
import asyncio

from Modules.buttons import update_buttons_on_start
from Modules.activity_monitoring import periodic_check_for_guilds
from Modules.db_control import read_from_guild_settings_db
from Modules.voice_channels_control import check_and_remove_nonexistent_channels

from utils import get_bot

bot = get_bot()

invitations = {}

async def start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()

    await update_buttons_on_start()
    await check_and_remove_nonexistent_channels()
    for guild in bot.guilds:
        invitations[guild.id] = await guild.invites()
    await periodic_check_for_guilds(bot)

async def join_from_invite(member):
    inviter = ''
    guild = member.guild
    invites_before = invitations[guild.id]
    invites_after = await guild.invites()

    for invite in invites_before:
        for after in invites_after:
            if invite.code == after.code:
                if invite.uses < after.uses:
                    inviter = invite.inviter
                    invite_code = invite.code
                    break


    # While there is no logging system on the server, the output is simply to the console via print
    if inviter:
        print(f'{member.name} joined via invitation {invite_code}, invited by {inviter.name}.')
    else:
        print(f'{member.name} joined without being invited by any other member.')

    # Обновляем информацию о приглашениях
    invitations[guild.id] = invites_after

async def greetings_delete_greetings(message):
    if message.reference and read_from_guild_settings_db(message.guild.id, 'removing_greetings')[0] =='on':
        delay = int(read_from_guild_settings_db(message.guild.id, 'removing_greetings_delay')[0])
        original_message = await message.channel.fetch_message(message.reference.message_id)
        if original_message.type == discord.MessageType.new_member and original_message.author in message.guild.members:
            await asyncio.sleep(delay)
            await message.delete()
        elif original_message.type == discord.MessageType.new_member and original_message.author not in message.guild.members:
            await message.delete()
            await original_message.delete()