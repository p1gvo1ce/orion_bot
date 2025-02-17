from utils import get_bot

bot = get_bot()

def read_values_from_file(file_path):
    """
    Читает числовые значения из текстового файла построчно.

    Parameters:
    - file_path (str): Путь к текстовому файлу.

    Returns:
    - list: Список числовых значений из файла.
    """
    values = []
    with open(file_path, 'r') as file:
        for line in file:
            try:
                value = int(line.strip())
                values.append(value)
            except ValueError:
                print(f"Ошибка при чтении значения из строки: {line}")
    return values

async def bolnoy_ublyudok(message):

    file_path_read = 'bub_block_ids.txt'
    bub_block_users = read_values_from_file(file_path_read)

    if message.author == bot.user:
        return

    text = message.content.lower()
    channel_bub = bot.get_channel(1196416516120379522)
    role = 1196412886944329738
    role = message.guild.get_role(role)
    if 'я' in text and 'больн' in text and 'ублюд' in text and 'не' not in text:
        if message.author.id in bub_block_users:
            await message.add_reaction('🖕')
            return
        if role.id not in [role.id for role in message.author.roles]:
            await message.author.add_roles(role)
            await channel_bub.send(f'''Привет <@{message.author.id}>!
Прежде всего чекни <#1196415511655895050> и если что-то не нравится - пиздуй отседова.
Если всё ок - заходи, ложись, здравствуй.''')
            await message.add_reaction('👉')
            await message.add_reaction('🤮')

    if 'я' in text and 'больн' in text and 'ублюд' in text and 'не' in text:
        if role.id in [role.id for role in message.author.roles]:
            await message.author.remove_roles(role)
            await channel_bub.send(f'''<@{message.author.id}> больше не больной ублюдок.
Поздравляем с этим и желаем усраться.''')