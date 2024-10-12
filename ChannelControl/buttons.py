import discord
import re
from phrases import get_phrase
from DataBase.db_control import (get_recent_activity_members, read_button_data_from_db, read_from_guild_settings_db,
                                 delete_button_data_from_db, read_all_buttons_data)
from utils import  clean_channel_id, get_bot

bot = get_bot()

async def update_buttons_on_start():
    # Читаем все записи из базы данных
    buttons_data = read_all_buttons_data()
    find_voices_ids = []
    for button_data in buttons_data:
        guild_id = button_data["server_id"]
        guild = bot.get_guild(guild_id)

        if guild:
            # Получаем канал, по которому мы знаем, что могло быть отправлено сообщение
            search_text_channel_ids = read_from_guild_settings_db(guild_id, "party_find_text_channel_id")
            search_text_channel_ids = [clean_channel_id(id_str) for id_str in search_text_channel_ids]

            # Ищем сообщение по его ID
            message = None
            for text_channel_id in search_text_channel_ids:
                text_channel = guild.get_channel(text_channel_id)
                if text_channel:
                    try:
                        # Пробуем получить сообщение по его ID
                        message = await text_channel.fetch_message(button_data["message_id"])
                        break
                    except discord.NotFound:
                        # Если сообщение не найдено в этом канале, продолжаем поиск в других каналах
                        continue

            if message:
                # Сообщение найдено, теперь обновляем кнопки
                member = guild.get_member(button_data["member_id"])
                voice_channel_id = extract_id(message.content)
                find_voices_ids.append(voice_channel_id)
                if member and member.voice:
                    if str(member.voice.channel.id) != voice_channel_id:
                        print(member.voice.channel.id)
                        print(voice_channel_id)
                        await message.delete()
                    else:
                        await message.edit(view=None)  # Удаляем старые кнопки

                        if button_data["button_type"] == "JoinButton":
                            invite = button_data["data"].get("invite")
                            await message.edit(view=JoinButton(invite, guild_id, member.activity.name, member.id))
                if not member.voice:
                    await message.delete()

            else:
                # Если сообщение не найдено, удаляем запись из базы данных
                delete_button_data_from_db(button_data["message_id"])

    for voice in guild.voice_channels:
        if str(voice.id) in find_voices_ids and len(voice.members) == 0:
            await voice.delete()


def extract_id(message):
    pattern = r"<#(\d+)>"
    match = re.search(pattern, message)
    if match:
        return match.group(1)
    return None

class AddInfoModal(discord.ui.Modal):
    def __init__(self, original_message, guild_id):
        super().__init__(title=get_phrase("Add Info", guild_id))
        self.original_message = original_message
        self.guild_id = guild_id

        # Поле ввода для информации (заменили на TextInput)
        self.add_item(discord.ui.TextInput(
            label=get_phrase("Additional Information", self.guild_id),
            placeholder=get_phrase("Enter any additional details here...", self.guild_id),
            max_length=200  # Ограничиваем длину сообщения
        ))

    async def on_submit(self, interaction: discord.Interaction):
        # Получаем введённый текст
        additional_info = self.children[0].value

        # Обновляем сообщение поиска, добавляя новую информацию
        updated_content = (f"{self.original_message.content}\n\n"
                           f"{get_phrase('Additional Information', self.guild_id)}:\n {additional_info}")
        await self.original_message.edit(content=updated_content)

        # Сообщаем пользователю об успешном добавлении
        await interaction.response.send_message(
            get_phrase("Information successfully added.", self.guild_id),
            ephemeral=True
        )


class JoinButton(discord.ui.View):
    def __init__(self, invite_url, guild_id, game, creator_id):
        super().__init__(timeout=None)
        self.invite_url = invite_url
        self.guild_id = guild_id
        self.creator_id = creator_id
        self.game = game

        # Кнопки остаются такими же
        join_button = discord.ui.Button(
            label=get_phrase("Join Voice Channel", self.guild_id),
            style=discord.ButtonStyle.success
        )
        join_button.callback = self.join_button_callback
        self.add_item(join_button)

        who_plays_button = discord.ui.Button(
            label=get_phrase("Who is playing?", self.guild_id),
            style=discord.ButtonStyle.primary
        )
        who_plays_button.callback = self.who_plays_button_callback
        self.add_item(who_plays_button)

        add_info_button = discord.ui.Button(
            label=get_phrase("Add Info", self.guild_id),
            style=discord.ButtonStyle.secondary
        )
        add_info_button.callback = self.add_info_button_callback
        self.add_item(add_info_button)

        close_button = discord.ui.Button(
            label=get_phrase("Close", self.guild_id),
            style=discord.ButtonStyle.danger
        )
        close_button.callback = self.close_button_callback
        self.add_item(close_button)

    async def join_button_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"{get_phrase('Click here to join', self.guild_id)}: {self.invite_url}",
            ephemeral=True
        )

    async def who_plays_button_callback(self, interaction: discord.Interaction):
        # Получаем активность текущего пользователя
        member = interaction.user

        # Ищем всех пользователей с той же активностью за последние 10 минут
        recent_members = get_recent_activity_members(self.guild_id, self.game, minutes=10)

        if recent_members:
            member_mentions = [f"<@{member_id}>" for member_id in recent_members]
            await interaction.response.send_message(
                f"{get_phrase('Currently playing', self.guild_id)}  '__**{self.game}**__':\n" + "\n".join(member_mentions),
                ephemeral=True
            )

    async def add_info_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message(
                get_phrase("Only the channel creator can add info.", self.guild_id),
                ephemeral=True
            )
            return

        # Открываем модальное окно для ввода информации
        modal = AddInfoModal(interaction.message, self.guild_id)
        await interaction.response.send_modal(modal)

    async def close_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message(
                get_phrase("Only the channel creator can close the search.", self.guild_id),
                ephemeral=True
            )
            return

        await interaction.message.delete()
        await interaction.response.send_message(
            get_phrase("Search message closed.", self.guild_id),
            ephemeral=True
        )