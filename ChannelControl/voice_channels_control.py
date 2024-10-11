import os
import json
import discord
import random
import asyncio
from DataBase.db_control import read_from_guild_settings_db, get_recent_activity_members
from ChannelControl.text_channels_control import add_game_in_game_roles_channel
from utils import clean_channel_id
from phrases import get_phrase

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


class AddInfoModal(discord.ui.Modal):
    def __init__(self, original_message, guild):
        super().__init__(title=get_phrase("Add Info", guild))
        self.original_message = original_message
        self.guild = guild

        # Поле ввода для информации (заменили на TextInput)
        self.add_item(discord.ui.TextInput(
            label=get_phrase("Additional Information", self.guild),
            placeholder=get_phrase("Enter any additional details here...", self.guild),
            max_length=200  # Ограничиваем длину сообщения
        ))

    async def on_submit(self, interaction: discord.Interaction):
        # Получаем введённый текст
        additional_info = self.children[0].value

        # Обновляем сообщение поиска, добавляя новую информацию
        updated_content = (f"{self.original_message.content}\n\n"
                           f"{get_phrase('Additional Information', self.guild)}:\n {additional_info}")
        await self.original_message.edit(content=updated_content)

        # Сообщаем пользователю об успешном добавлении
        await interaction.response.send_message(
            get_phrase("Information successfully added.", self.guild),
            ephemeral=True
        )


class JoinButton(discord.ui.View):
    def __init__(self, invite, guild, game, creator: discord.Member):
        super().__init__(timeout=None)
        self.invite = invite
        self.guild = guild
        self.creator = creator
        self.game = game

        # Кнопки остаются такими же
        join_button = discord.ui.Button(
            label=get_phrase("Join Voice Channel", self.guild),
            style=discord.ButtonStyle.success
        )
        join_button.callback = self.join_button_callback
        self.add_item(join_button)

        who_plays_button = discord.ui.Button(
            label=get_phrase("Who is playing?", self.guild),
            style=discord.ButtonStyle.primary
        )
        who_plays_button.callback = self.who_plays_button_callback
        self.add_item(who_plays_button)

        add_info_button = discord.ui.Button(
            label=get_phrase("Add Info", self.guild),
            style=discord.ButtonStyle.secondary
        )
        add_info_button.callback = self.add_info_button_callback
        self.add_item(add_info_button)

        close_button = discord.ui.Button(
            label=get_phrase("Close", self.guild),
            style=discord.ButtonStyle.danger
        )
        close_button.callback = self.close_button_callback
        self.add_item(close_button)

    async def join_button_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"{get_phrase('Click here to join', self.guild)}: {self.invite.url}",
            ephemeral=True
        )

    async def who_plays_button_callback(self, interaction: discord.Interaction):
        # Получаем активность текущего пользователя
        member = interaction.user

        # Ищем всех пользователей с той же активностью за последние 10 минут
        recent_members = get_recent_activity_members(member.guild.id, self.game, minutes=10)

        if recent_members:
            member_mentions = [member.guild.get_member(int(member_id)).mention for member_id in recent_members]
            await interaction.response.send_message(
                f"{get_phrase('Currently playing', self.guild)}  '__**{self.game}**__':\n" + "\n".join(member_mentions),
                ephemeral=True
            )

    async def add_info_button_callback(self, interaction: discord.Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                get_phrase("Only the channel creator can add info.", self.guild),
                ephemeral=True
            )
            return

        # Открываем модальное окно для ввода информации
        modal = AddInfoModal(interaction.message, self.guild)
        await interaction.response.send_modal(modal)

    async def close_button_callback(self, interaction: discord.Interaction):
        if interaction.user != self.creator:
            await interaction.response.send_message(
                get_phrase("Only the channel creator can close the search.", self.guild),
                ephemeral=True
            )
            return

        await interaction.message.delete()
        await interaction.response.send_message(
            get_phrase("Search message closed.", self.guild),
            ephemeral=True
        )

async def find_party_controller(member, before, after):
    guild_id = member.guild.id
    guild = member.guild

    # Проверяем, подключился ли участник к новому каналу
    if after.channel and after.channel != before.channel:
        voice_channel_id = after.channel.id

        # Чтение данных о поисковых каналах из базы данных
        search_voice_channel_ids = read_from_guild_settings_db(guild_id, "party_find_voice_channel_id")
        search_voice_channel_ids = [clean_channel_id(id_str) for id_str in search_voice_channel_ids]

        if voice_channel_id in search_voice_channel_ids:

            if member.activity and member.activity.type == discord.ActivityType.playing:
                channel_name = member.activity.name
                role_name = channel_name
                role = discord.utils.get(after.channel.guild.roles, name=role_name)

                if role is None:
                    random_color = random.randint(0, 0xFFFFFF)
                    role = await after.channel.guild.create_role(name=role_name, color=discord.Color(random_color))
                    await add_game_in_game_roles_channel(role, after.channel.guild)

                if role not in member.roles:
                    await member.add_roles(role)

            else:
                channel_name = member.nick if member.nick else member.name

            if len(channel_name) > 100:
                channel_name = channel_name[:100]

            max_bitrate = after.channel.guild.bitrate_limit

            temp_channel = await after.channel.guild.create_voice_channel(
                channel_name,
                bitrate=max_bitrate
            )

            overwrite = discord.PermissionOverwrite()
            overwrite.update(
                manage_channels=True,
                mute_members=True,
                move_members=True,
                manage_permissions=True
            )
            await temp_channel.set_permissions(member, overwrite=overwrite)
            await member.move_to(temp_channel)

            temp_channels = load_temp_channels()
            temp_channels[str(temp_channel.id)] = {"guild_id": guild_id}
            save_temp_channels(temp_channels)
            if member.activity and member.activity.type == discord.ActivityType.playing:
                search_text_channel_ids = read_from_guild_settings_db(guild_id, "party_find_text_channel_id")
                search_text_channel_ids = [clean_channel_id(id_str) for id_str in search_text_channel_ids]

                invite = await temp_channel.create_invite(max_age=3600, max_uses=99)  # Создаем приглашение

                for text_channel_id in search_text_channel_ids:
                    text_channel = member.guild.get_channel(text_channel_id)
                    if text_channel:
                        find_message = await text_channel.send(
                            content=f"{member.mention} {get_phrase('looking for a company', guild)} "
                                    f"{temp_channel.mention}.\n"
                                    f"<@&{role.id}>",
                            view=JoinButton(invite, guild, member.activity.name, member)
                        )
                        break

                asyncio.create_task(check_member_in_channel(member, temp_channel, find_message, invite))

    if before.channel and before.channel != after.channel:
        temp_channels = load_temp_channels()
        if str(before.channel.id) in temp_channels:
            if len(before.channel.members) == 0:
                await before.channel.delete()
                del temp_channels[str(before.channel.id)]
                save_temp_channels(temp_channels)

# Проверка наличия участника в голосовом (актуальность поиска)
async def check_member_in_channel(member, temp_channel, find_message, invite):
    while True:
        await asyncio.sleep(60)

        if member not in temp_channel.members:
            try:
                await find_message.delete()
            except discord.NotFound:
                pass
            break