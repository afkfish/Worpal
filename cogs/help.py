from discord import Interaction, Embed, app_commands, ui, ButtonStyle, InteractionMessage
from discord.ext import commands

from main import Worpal


class Navigation(ui.View):
    def __init__(self, bot: Worpal, original_interaction: Interaction):
        super().__init__(timeout=180)
        self.bot = bot
        self.original_interaction = original_interaction
        self.page = 0
        self.max = 3

    @ui.button(emoji="⬅️", style=ButtonStyle.grey, disabled=True)
    async def prev(self, interaction: Interaction, button: ui.Button):
        if self.page >= 1:
            self.page -= 1
            for item in self.children:
                if isinstance(item, ui.Button):
                    item.disabled = False

        if self.page <= 0:
            button.disabled = True
            self.page = 0

        await interaction.response.edit_message(embed=Help.get_page(self.page), view=self)

    @ui.button(emoji="➡️", style=ButtonStyle.grey)
    async def next(self, interaction: Interaction, button: ui.Button):
        if self.page < self.max:
            self.page += 1
            for item in self.children:
                if isinstance(item, ui.Button):
                    item.disabled = False

        if self.page >= self.max:
            button.disabled = True
            self.page = self.max

        await interaction.response.edit_message(embed=Help.get_page(self.page), view=self)

    @ui.button(emoji="❌", style=ButtonStyle.grey)
    async def delete(self, interaction: Interaction, button: ui.Button):
        self.stop()
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True

        message: InteractionMessage = await self.original_interaction.original_response()
        await message.delete()


class Help(commands.Cog):

    def __init__(self, bot: Worpal):
        self.bot = bot

    @app_commands.command(name="help", description="help info")
    async def help(self, interaction: Interaction):
        await interaction.response.defer()
        view = Navigation(self.bot, interaction)
        embed = self.get_page(0)
        await interaction.followup.send(embed=embed, view=view)
        await view.wait()

    #         # case "lyrics":
    #         # 	embed.title = "Lyrics"
    #         # 	embed.add_field(name="Usage:", value="The lyrics command tries to find the song on genius and sends "
    #         # 										 "back the lyrics if it succeded. Not every song will 100% have a "
    #         # 										 "lyric. If you are sure it has, but it is not available on genius "
    #         # 										 "than the subtitle command could help.")
    #         # case "ping":
    #         # 	embed.title = "Ping"
    #         # 	embed.add_field(name="Usage:", value="The ping command measures the latency from the server to the "
    #         # 										 "client in miliseconds.")

    @staticmethod
    def get_page(n: int) -> Embed:
        embed = Embed(title=f"Help", color=Worpal.color)
        embed.set_footer(text=f"Page {n + 1}/4")

        match n:
            case 0:
                embed.add_field(name="Play :arrow_forward:",
                                value="The play command accepts words, youtube links, spotify links to "
                                      "songs and playlists (only the first 10 song will be added from "
                                      "them to the playlist) as an argument. "
                                      "The user must be in a voice channel when executing the command! "
                                      "The bot cannot play livestreams or videos that are age "
                                      "restricted! "
                                      "The bot will search for a video named as the argument or the "
                                      "link, or in case of a spotify link then on spotify and "
                                      "try to stream it into the voice channel where the user is "
                                      "present.",
                                inline=False)
                embed.add_field(name="Skip :next_track:",
                                value="The skip command allows the user to skip a track when the bot "
                                      "is playing. If nothing is in the queue then the bot will stop.",
                                inline=False)
            case 1:
                embed.add_field(name="Pause :pause_button:",
                                value="The pause command has no parameters. It tries to stop the music "
                                      "if the bot is playing.",
                                inline=False)
                embed.add_field(name="Resume",
                                value="The resume command resumes the music if it has been paused.",
                                inline=False)
                embed.add_field(name="Stop :stop_button:",
                                value="The stop command stops the media playing and clears the queue. "
                                      "The next song in the queue can be played once a new song is "
                                      "added by a play command.",
                                inline=False)
            case 2:
                embed.add_field(name="Queue",
                                value="The queue command sends an embed displaying the previously "
                                      "added tracks that will be played.",
                                inline=False)
                embed.add_field(name="Clear duplicates",
                                value="The clear duplicates command removes the duplicated songs from "
                                      "the queue if there are any.",
                                inline=False)
                embed.add_field(name="Clear all",
                                value="The clear all command empties the queue completely.",
                                inline=False)
            case 3:
                embed.add_field(name="Now Playing",
                                value="The np command sends an embed representing the music that is "
                                      "currently being played. If the music stopped or skipped but the "
                                      "queue is empty than the previously played song will be sent.",
                                inline=False)
                embed.add_field(name="Leave",
                                value="The leave command disconnects the bot from the voice channel if "
                                      "it was in one.",
                                inline=False)
            case _:
                embed.add_field(name="¿¿¿error???", value="¿¿¿???")

        return embed


async def setup(bot):
    await bot.add_cog(Help(bot))
