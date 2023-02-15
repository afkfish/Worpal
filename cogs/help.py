from discord import Interaction, Embed, app_commands
from discord.ext import commands

from main import Worpal


class Help(commands.GroupCog, name="help"):

    def __init__(self, bot: Worpal):
        self.bot = bot

    async def help_embed(self, interaction: Interaction, command: str):
        await interaction.response.defer()
        embed = Embed(color=0x152875)
        embed.set_author(name="Worpal", icon_url=self.bot.icon)
        match command:
            case "play":
                embed.title = "Play :arrow_forward:"
                embed.add_field(name="Usage:", value="The play command accepts words, youtube links, spotify links to "
                                                     "songs and playlists (only the first 10 song will be added from "
                                                     "them to the queue) as an argument. "
                                                     "The user must be in a voice channel when executing the command! "
                                                     "The bot cannot play livestreams and videos that are age "
                                                     "restricted! "
                                                     "The bot will search for a video named as the argument or the "
                                                     "link, or in case of a spotify link then on spotify and "
                                                     "try to stream it into the voice channel where the user is "
                                                     "present.")
            case "queue":
                embed.title = "Queue"
                embed.add_field(name="Usage:", value="The queue command sends an embed displaying the previously "
                                                     "added tracks that will be played.")
            case "skip":
                embed.title = "Skip :next_track:"
                embed.add_field(name="Usage:", value="The skip command allows the user to skip a track when the bot "
                                                     "is playing. If nothing is in the queue then the bot will stop.")
            case "pause":
                embed.title = "Pause :pause_button:"
                embed.add_field(name="Usage:", value="The pause command has no parameters. It tries to stop the music "
                                                     "if the bot is playing.")
            case "resume":
                embed.title = "Resume"
                embed.add_field(name="Usage:", value="The resume command resumes the music if it has been paused.")
            case "stop":
                embed.title = "Stop :stop_button:"
                embed.add_field(name="Usage:", value="The stop command stops the media playing and clears the queue. "
                                                     "The next song in the queue can be played once a new song is "
                                                     "added by a play command.")
            case "leave":
                embed.title = "Leave"
                embed.add_field(name="Usage:", value="The leave command disconnects the bot from the voice channel if "
                                                     "it was in one.")
            case "clear duplicates":
                embed.title = "Clear duplicates"
                embed.add_field(name="Usage:", value="The clear duplicates command removes the duplicated songs from "
                                                     "the queue if there are any.")
            case "clear all":
                embed.title = "Clear all"
                embed.add_field(name="Usage:", value="The clear all command empties the queue completely.")
            case "np":
                embed.title = "Now Playing"
                embed.add_field(name="Usage:", value="The np command sends an embed representing the music that is "
                                                     "currently being played. If the music stopped or skipped but the "
                                                     "queue is empty than the previously played song will be sent.")
            # case "lyrics":
            # 	embed.title = "Lyrics"
            # 	embed.add_field(name="Usage:", value="The lyrics command tries to find the song on genius and sends "
            # 										 "back the lyrics if it succeded. Not every song will 100% have a "
            # 										 "lyric. If you are sure it has but it is not available on genius "
            # 										 "than the subtitle command could help.")
            # case "ping":
            # 	embed.title = "Ping"
            # 	embed.add_field(name="Usage:", value="The ping command measures the latency from the server to the "
            # 										 "client in miliseconds.")
            case _:
                pass
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="play", description="play command")
    async def help_play(self, interaction: Interaction):
        await self.help_embed(interaction, "play")

    @app_commands.command(name="queue", description="queue command")
    async def help_queue(self, interaction: Interaction):
        await self.help_embed(interaction, "queue")

    @app_commands.command(name="skip", description="skip command")
    async def help_skip(self, interaction: Interaction):
        await self.help_embed(interaction, "skip")

    @app_commands.command(name="pause", description="pause command")
    async def help_pause(self, interaction: Interaction):
        await self.help_embed(interaction, "pause")

    @app_commands.command(name="resume", description="resume command")
    async def help_resume(self, interaction: Interaction):
        await self.help_embed(interaction, "resume")

    @app_commands.command(name="stop", description="stop command")
    async def help_stop(self, interaction: Interaction):
        await self.help_embed(interaction, "stop")

    @app_commands.command(name="leave", description="leave command")
    async def help_leave(self, interaction: Interaction):
        await self.help_embed(interaction, "leave")

    @app_commands.command(name="clear_dumplicates", description="clear duplicates command")
    async def help_clear_d(self, interaction: Interaction):
        await self.help_embed(interaction, "clear duplicates")

    @app_commands.command(name="clear_all", description="clear all command")
    async def help_clear_a(self, interaction: Interaction):
        await self.help_embed(interaction, "clear all")

    @app_commands.command(name="np", description="np command")
    async def help_np(self, interaction: Interaction):
        await self.help_embed(interaction, "np")

# @app_commands.command(name="lyrics", description="lyrics command")
# async def help_lyrics(self, interaction: Interaction):
#     await self.help_embed(interaction=interaction, command="lyrics")
#
# @app_commands.command(name="ping", description="ping command")
# async def help_ping(self, interaction: Interaction):
# 	await self.help_embed(interaction=interaction, command="ping")


async def setup(bot):
    await bot.add_cog(Help(bot))
