import discord
import re

from matplotlib.style.core import context

from Modules.phrases import get_phrase
from Modules.db_control import (get_recent_activity_members, read_from_guild_settings_db,
                                delete_button_data_from_db, read_all_buttons_data, write_to_buttons_db)
from utils import  clean_channel_id, get_bot

bot = get_bot()

async def update_buttons_on_start():
    buttons_data = read_all_buttons_data()
    find_voices_ids = []
    for button_data in buttons_data:
        guild_id = button_data["server_id"]
        guild = bot.get_guild(guild_id)

        if guild:
            search_text_channel_ids = read_from_guild_settings_db(guild_id, "party_find_text_channel_id")
            search_text_channel_ids = [clean_channel_id(id_str) for id_str in search_text_channel_ids]

            message = None
            for text_channel_id in search_text_channel_ids:
                text_channel = guild.get_channel(text_channel_id)
                if text_channel:
                    try:
                        message = await text_channel.fetch_message(button_data["message_id"])
                        break
                    except discord.NotFound:
                        continue

            if message:
                if button_data["button_type"] == "JoinButton":
                    member = guild.get_member(button_data["member_id"])
                    voice_channel_id = extract_id(message.content)
                    find_voices_ids.append(voice_channel_id)
                    if member and member.voice:
                        if str(member.voice.channel.id) != voice_channel_id:
                            print(member.voice.channel.id)
                            print(voice_channel_id)
                            await message.delete()
                        else:
                            await message.edit(view=None)


                    invite = button_data["data"].get("invite")
                    try:
                        activity = member.activity.name
                    except:
                        activity = 'None'
                    await message.edit(view=JoinButton(invite, guild_id, activity, member.id))
                    if not member.voice:
                        await message.delete()

                elif button_data["button_type"] == "FindPartyWithoutActivity":
                    await message.edit(view=None)
                    await message.edit(view=FindPartyWithoutActivity(guild))


            else:
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

class FindInfoModal(discord.ui.Modal):
    def __init__(self, original_message, guild, member):
        super().__init__(title=get_phrase("create_find", guild.id))
        self.original_message = original_message
        self.guild_id = guild.id
        self.guild = guild
        self.activity_name = ''
        self.activity_info = ''
        self.member = member

        self.add_item(discord.ui.TextInput(
            label=get_phrase("Activity name", self.guild_id),
            placeholder=get_phrase("Enter the activity name here", self.guild_id),
            max_length=200
        ))
        self.add_item(discord.ui.TextInput(
            label=get_phrase("Additional Information", self.guild_id),
            placeholder=get_phrase("Enter any additional details here...", self.guild_id),
            max_length=200
        ))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        self.activity_name = self.children[0].value
        self.activity_info = self.children[1].value

        role = discord.utils.get(self.guild.roles, name=self.activity_name)
        if role:
            activity = f"<@&{role.id}>"
        else:
            activity = '## ' + self.activity_name
        find_message = await interaction.channel.send(
            content=f"{self.member.mention} {get_phrase('looking for a company', self.guild)} "
                    f"{self.member.voice.channel.mention}.\n"
                    f"{activity}\n\n"
                    f"{get_phrase('Additional Information', self.guild_id)}:\n"
                    f"{self.activity_info}"
        )
        invite = await self.member.voice.channel.create_invite(max_age=3600, max_uses=99)
        invite_data = {"invite": invite.url}
        write_to_buttons_db(self.guild.id, find_message.id, "JoinButton", invite_data, self.member.id)

        await find_message.edit(view=JoinButton(invite.url, self.guild.id, self.activity_name, self.member.id))

class FindPartyWithoutActivity(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

        how_to_search = discord.ui.Button(
            label=get_phrase("How to search", self.guild.id),
            style=discord.ButtonStyle.secondary
        )
        how_to_search.callback = self.how_to_search
        self.add_item(how_to_search)

        create_find = discord.ui.Button(
            label=get_phrase("create_find", self.guild.id),
            style=discord.ButtonStyle.success
        )
        create_find.callback = self.create_find
        self.add_item(create_find)

    async def how_to_search(self, interaction: discord.Interaction):

        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        description = get_phrase('how_to_search_instruction', self.guild.id)
        embed.description = description

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )



    async def create_find(self, interaction: discord.Interaction):
        member = interaction.user
        if not member.voice:
            embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
            description = get_phrase('You must be in the voice channel.', self.guild.id)
            embed.description = description

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
        else:
            async for message in interaction.channel.history(limit=20):
                if str(member.id) in message.content:
                    embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
                    description = get_phrase('You cannot run more than 1 search per person.', self.guild.id)
                    embed.description = description

                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    return
            modal = FindInfoModal(interaction.message, self.guild, member)
            await interaction.response.send_modal(modal)

class AddInfoModal(discord.ui.Modal):
    def __init__(self, original_message, guild_id):
        super().__init__(title=get_phrase("Add Info", guild_id))
        self.original_message = original_message
        self.guild_id = guild_id

        # Поле ввода для информации (заменили на TextInput)
        self.add_item(discord.ui.TextInput(
            label=get_phrase("Additional Information", self.guild_id),
            placeholder=get_phrase("Enter any additional details here...", self.guild_id),
            max_length=200
        ))

    async def on_submit(self, interaction: discord.Interaction):
        additional_info = self.children[0].value

        updated_content = (f"{self.original_message.content}\n\n"
                           f"{get_phrase('Additional Information', self.guild_id)}:\n {additional_info}")
        await self.original_message.edit(content=updated_content)

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
        embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
        description = get_phrase('Click here to join', self.guild_id)
        embed.description = description

        await interaction.response.send_message(
            content = self.invite_url,
            embed=embed,
            ephemeral=True
        )

    async def who_plays_button_callback(self, interaction: discord.Interaction):
        member = interaction.user
        if self.game == 'None':
            embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
            description = get_phrase('There is no information on this activity.', self.guild_id)
            embed.description = description

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            return

        recent_members = get_recent_activity_members(self.guild_id, self.game, minutes=10)
        if recent_members:
            member_mentions = [f"<@{member_id}>" for member_id in recent_members]
            embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
            description = f"{get_phrase('Currently playing', self.guild_id)}  '__**{self.game}**__':\n" + "\n".join(member_mentions)
            embed.description = description

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
        else:
            embed = discord.Embed(color=discord.Color.from_str("#EE82EE"))
            description = get_phrase('No one has been seen playing this game lately.', self.guild_id)
            embed.description = description

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

    async def add_info_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message(
                get_phrase("Only the channel creator can add info.", self.guild_id),
                ephemeral=True
            )
            return

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