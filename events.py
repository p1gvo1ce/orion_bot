from ChannelControl.buttons import update_buttons_on_start
from ActivityControl.activity_monitoring import periodic_check_for_guilds

from utils import get_bot

bot = get_bot()

# Словарь для хранения приглашений
invitations = {}

async def start():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()

    await update_buttons_on_start()

    for guild in bot.guilds:
        invitations[guild.id] = await guild.invites()
    await periodic_check_for_guilds(bot)

async def join_from_invite(member):
    guild = member.guild
    invites_before = invitations[guild.id]
    invites_after = await guild.invites()

    # Сравниваем приглашения, чтобы найти, по какому пригласили участника
    for invite in invites_before:
        for after in invites_after:
            if invite.code == after.code:
                # Если количество использований изменилось
                if invite.uses < after.uses:
                    inviter = invite.inviter
                    invite_code = invite.code
                    break
    if inviter:
        print(f'{member.name} joined via invitation {invite_code}, invited by {inviter.name}.')
    else:
        print(f'{member.name} joined without being invited by any other member.')

    # Обновляем информацию о приглашениях
    invitations[guild.id] = invites_after