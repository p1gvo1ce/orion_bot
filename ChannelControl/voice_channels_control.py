import os
import json
import discord
import random
from DataBase.db_control import read_from_guild_settings_db
from ChannelControl.text_channels_control import add_game_in_game_roles_channel
from utils import clean_channel_id

temp_channels_path = os.path.join("ChannelControl", "temp_channels.json")

# Функция для загрузки временных каналов из JSON
def load_temp_channels():
    if os.path.exists(temp_channels_path):
        with open(temp_channels_path, "r") as f:
            return json.load(f)
    return {}

# Функция для сохранения временных каналов в JSON
def save_temp_channels(temp_channels):
    os.makedirs(os.path.dirname(temp_channels_path), exist_ok=True)
    with open(temp_channels_path, "w") as f:
        json.dump(temp_channels, f, indent=4)


# Функция контроля поиска пати
async def find_party_controller(member, before, after):
    guild_id = member.guild.id

    # Проверяем, подключился ли участник к новому каналу
    if after.channel and after.channel != before.channel:
        voice_channel_id = after.channel.id

        # Чтение данных о поисковых каналах из базы данных
        search_voice_channel_ids = read_from_guild_settings_db(guild_id, "party_find_voice_channel_id")
        search_voice_channel_ids = [clean_channel_id(id_str) for id_str in search_voice_channel_ids]
        # Проверяем, является ли текущий канал одним из поисковых
        if voice_channel_id in search_voice_channel_ids:

            if member.activity and member.activity.type == discord.ActivityType.playing:
                channel_name = member.activity.name

                # Проверка и управление ролью активности
                role_name = channel_name  # Имя роли будет таким же, как имя канала
                role = discord.utils.get(after.channel.guild.roles, name=role_name)

                if role is None:
                    # Если роли нет, создаем её с случайным цветом
                    random_color = random.randint(0, 0xFFFFFF)  # Генерируем случайный цвет
                    role = await after.channel.guild.create_role(name=role_name, color=discord.Color(random_color))

                    await add_game_in_game_roles_channel(role, after.channel.guild)

                # Проверяем, есть ли у участника роль
                if role not in member.roles:
                    await member.add_roles(role)  # Добавляем роль участнику

            else:
                channel_name = member.nick if member.nick else member.name

            if len(channel_name) > 100:
                channel_name = channel_name[:100]

            max_bitrate = after.channel.guild.bitrate_limit

            temp_channel = await after.channel.guild.create_voice_channel(
                channel_name,
                bitrate=max_bitrate  # Устанавливаем максимальный битрейт
            )

            # Права для создателя канала (чтобы мог управлять каналом)
            overwrite = discord.PermissionOverwrite()
            overwrite.update(
                manage_channels=True,  # Управление каналом (изменение названия и настроек)
                mute_members=True,  # Мут участников
                move_members=True,  # Перемещение участников
                manage_permissions=True  # Управление правами доступа
            )

            # Устанавливаем права для участника, который создал канал
            await temp_channel.set_permissions(member, overwrite=overwrite)

            # Перемещаем участника в временный канал
            await member.move_to(temp_channel)

            # Добавляем временный канал в JSON
            temp_channels = load_temp_channels()
            temp_channels[str(temp_channel.id)] = {"guild_id": guild_id}
            save_temp_channels(temp_channels)

            # Чтение текстовых поисковых каналов из базы данных
            search_text_channel_ids = read_from_guild_settings_db(guild_id, "party_find_text_channel_id")
            search_text_channel_ids = [clean_channel_id(id_str) for id_str in search_text_channel_ids]

            # Ищем первый существующий текстовый канал и отправляем туда сообщение
            for text_channel_id in search_text_channel_ids:
                text_channel = member.guild.get_channel(text_channel_id)
                if text_channel:  # Проверяем, существует ли канал
                    await text_channel.send(
                        f"{member.mention} был перемещен в {temp_channel.mention} для поиска группы.")
                    break  # Найдя существующий канал, прерываем цикл

        # Проверка, отключился ли участник из временного канала
    if before.channel and before.channel != after.channel:
        temp_channels = load_temp_channels()

        # Если канал был временным и больше никого не осталось, удаляем канал
        if str(before.channel.id) in temp_channels:
            if len(before.channel.members) == 0:
                await before.channel.delete()
                del temp_channels[str(before.channel.id)]
                save_temp_channels(temp_channels)