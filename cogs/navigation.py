from discord import app_commands, Interaction, VoiceClient, Embed, User
from discord.ext import commands

from cogs.play import slist, Play
from main import Worpal


class Navigation(commands.Cog):

    def __init__(self, bot: Worpal):
        self.bot = bot
        self.ctx_skip = app_commands.ContextMenu(
            name="Skip",
            callback=self.skip
        )
        self.bot.tree.add_command(self.ctx_skip)
        # TODO: fix this bugged thing
        # self.ctx_pause = app_commands.ContextMenu(
        #     name="Pause",
        #     callback=self.pause
        # )
        # self.bot.tree.add_command(self.ctx_pause)
        # self.ctx_resume = app_commands.ContextMenu(
        #     name="Resume",
        #     callback=self.resume
        # )
        # self.bot.tree.add_command(self.ctx_resume)
        # self.ctx_stop = app_commands.ContextMenu(
        #     name="Stop",
        #     callback=self.stop
        # )
        # self.bot.tree.add_command(self.ctx_stop)
        # self.ctx_leave = app_commands.ContextMenu(
        #     name="Leave",
        #     callback=self.leave
        # )
        # self.bot.tree.add_command(self.ctx_leave)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_skip.name, type=self.ctx_skip.type)
        # self.bot.tree.remove_command(self.ctx_pause.name, type=self.ctx_pause.type)
        # self.bot.tree.remove_command(self.ctx_resume.name, type=self.ctx_resume.type)
        # self.bot.tree.remove_command(self.ctx_stop.name, type=self.ctx_stop.type)
        # self.bot.tree.remove_command(self.ctx_leave.name, type=self.ctx_leave.type)

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip_command(self, interaction: Interaction) -> None:
        await self.skip(interaction)

    async def skip(self, interaction: Interaction, user: User = None) -> None:
        await interaction.response.defer()
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            voice.stop()
            await Play(self.bot).play_music(interaction)
            await interaction.followup.send(embed=Embed(title="Skipped :next_track:", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="I'm not playing anything", color=Worpal.color))

    @app_commands.command(name="pause", description="Pause the song")
    async def pause_command(self, interaction: Interaction) -> None:
        await self.pause(interaction)

    @staticmethod
    async def pause(interaction: Interaction, user: User = None) -> None:
        await interaction.response.defer()
        voice: VoiceClient = interaction.guild.voice_client
        if voice and voice.is_playing():
            voice.pause()
            await interaction.followup.send(embed=Embed(title="Paused :pause_button:", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="I'm not playing anything", color=Worpal.color))

    @app_commands.command(name="resume", description="Resume playing")
    async def resume_command(self, interaction: Interaction) -> None:
        await self.resume(interaction)

    @staticmethod
    async def resume(interaction: Interaction, user: User = None) -> None:
        await interaction.response.defer()
        voice: VoiceClient = interaction.guild.voice_client
        if voice and voice.is_paused():
            voice.resume()
            await interaction.followup.send(embed=Embed(title="Resumed :arrow_forward:", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="Playing is not paused", color=Worpal.color))

    @app_commands.command(name="stop", description="Stop playing")
    async def stop_command(self, interaction: Interaction) -> None:
        await self.stop(interaction)

    async def stop(self, interaction: Interaction, user: User = None) -> None:
        await interaction.response.defer()
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            voice.stop()
            self.bot.music_queue[interaction.guild.id] = []
            await interaction.followup.send(embed=Embed(title="Stopped :stop_button:", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="Error!", color=Worpal.color))

    @app_commands.command(name="leave", description="Leave voice chat")
    async def leave_command(self, interaction: Interaction) -> None:
        await self.leave(interaction)

    async def leave(self, interaction: Interaction, user: User = None) -> None:
        await interaction.response.defer(ephemeral=True)
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            await voice.disconnect()
            self.bot.playing[interaction.guild.id] = None
            self.bot.music_queue[interaction.guild.id] = []
            await interaction.followup.send(embed=Embed(title="Disconnected!", color=Worpal.color), ephemeral=True)
            return

        await interaction.followup.send(embed=Embed(title="I'm not connected to a voice channel", color=Worpal.color),
                                        ephemeral=True)

    clear = app_commands.Group(name="clear", description="...")

    @clear.command(name="duplicates", description="Clear duplicated songs from queue.")
    async def clear_dup(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        if self.bot.music_queue[interaction.guild.id]:
            res = list(dict.fromkeys(self.bot.music_queue[interaction.guild.id]))
            self.bot.music_queue[interaction.guild.id] = res

        embed = Embed(title="Duplicated songs cleared! :broom:", color=Worpal.color)
        songs = slist(self.bot, interaction)

        if songs:
            embed.add_field(name="Songs: ", value=songs, inline=True)
        else:
            embed.add_field(name="Songs: ", value="No music in queue", inline=True)
        await interaction.followup.send(embed=embed)

    @clear.command(name="all", description="Clear all songs from queue.")
    async def clear_all(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        if self.bot.music_queue[interaction.guild.id]:
            self.bot.music_queue[interaction.guild.id] = []

        await interaction.followup.send(embed=Embed(title="Queue cleared! :broom:", color=Worpal.color))


async def setup(bot):
    await bot.add_cog(Navigation(bot))
