import datetime as dt

from discord import app_commands, Embed, ui, ButtonStyle, Interaction
from discord.ext import commands

from api.YouTubeAPI import youtube_api_search
from cogs.play import Play
from main import Worpal
from structures.playable import Track


class Selector(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @ui.button(label="1", style=ButtonStyle.grey)
    async def first(self, button: ui.Button, interaction):
        self.value = 1
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        self.stop()

    @ui.button(label="2", style=ButtonStyle.grey)
    async def second(self, button: ui.Button, interaction):
        self.value = 2
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        self.stop()

    @ui.button(label="3", style=ButtonStyle.grey)
    async def third(self, button: ui.Button, interaction):
        self.value = 3
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        self.stop()

    @ui.button(label="4", style=ButtonStyle.grey)
    async def fourth(self, button: ui.Button, interaction):
        self.value = 4
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        self.stop()

    @ui.button(label="5", style=ButtonStyle.grey)
    async def fifth(self, button: ui.Button, interaction):
        self.value = 5
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        self.stop()


class Search(commands.Cog):
    def __int__(self, bot: Worpal):
        self.bot = bot

    @app_commands.command(name="search", description="Search for a song on youtube.")
    async def search_(self, interaction: Interaction, q: str):
        await interaction.response.defer()
        songs = await youtube_api_search(Track(q, interaction.user))
        if songs:
            view = Selector()
            embed = Embed(title=f"Search results for {q}", color=0x152875)
            embed.set_author(name="Worpal", icon_url=self.bot.icon)
            cropped = [{'source': song['formats'][0]['url'], 'title': song['title'], 'thumbnail': song['thumbnail'],
                        'duration': song['duration']} for song in songs]
            a = ""
            i = 0
            for i, entry in enumerate(cropped, i):
                a += f"{i + 1}. {entry['title']}\n\n"
            embed.add_field(name="Results:", value=a)
            await interaction.followup.send(embed=embed, view=view)
            await view.wait()
            if interaction.user.voice:
                voice_channel = interaction.user.voice.channel
                if view.value is not None:
                    self.bot.music_queue[interaction.guild_id].append([cropped[view.value - 1], voice_channel])
                    embed = Embed(title="Song added from search", color=0x152875)
                    embed.set_thumbnail(url=self.bot.music_queue[interaction.guild_id][-1][0]['thumbnail'])
                    embed.add_field(name=self.bot.music_queue[interaction.guild_id][-1][0]['title'],
                                    value=str(dt.timedelta(
                                        seconds=int(self.bot.music_queue[interaction.guild_id][-1][0]['duration']))),
                                    inline=True)
                    embed.set_footer(text="Song requested by: " + interaction.user.name)
                    await interaction.followup.send(embed=embed)
                    await Play(self.bot).play_audio(interaction)

            else:
                await interaction.followup.send(content="Connect to a voice channel!", ephemeral=True)

        else:
            await interaction.followup.send(content="Error in getting the videos!")


def setup(bot):
    bot.add_cog(Search(bot))
