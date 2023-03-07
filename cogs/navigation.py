from discord import app_commands, Interaction, VoiceClient, Embed, User
from discord.ext import commands

from cogs.play import slist, Play
from main import Worpal


class Navigation(commands.Cog):

    def __init__(self, bot: Worpal):
        self.bot = bot
        self.ctx_menus = [
            app_commands.ContextMenu(
                name="Skip",
                callback=self.skip
            ),
            app_commands.ContextMenu(
                name="Pause",
                callback=self.pause
            ),
            app_commands.ContextMenu(
                name="Resume",
                callback=self.resume
            ),
            app_commands.ContextMenu(
                name="Stop",
                callback=self.stop
            ),
            app_commands.ContextMenu(
                name="Leave",
                callback=self.leave
            )
        ]
        for ctx_menu in self.ctx_menus:
            self.bot.tree.add_command(ctx_menu)

    async def cog_unload(self) -> None:
        for ctx_menu in self.ctx_menus:
            self.bot.tree.remove_command(ctx_menu.name, type=ctx_menu.type)

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

    async def pause(self, interaction: Interaction, user: User = None) -> None:
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

    async def resume(self, interaction: Interaction, user: User = None) -> None:
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

        await interaction.followup.send(embed=Embed(title="I'm not playing anything", color=Worpal.color))

    @app_commands.command(name="sutup", description="Leave voice chat")
    async def sutup_command(self, interaction: Interaction) -> None:
        await self.sutup(interaction)

    async def sutup(self, interaction: Interaction, user: User = None) -> None:
        await interaction.response.defer(ephemeral=True)
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            await voice.disconnect()
            self.bot.playing[interaction.guild.id] = None
            self.bot.music_queue[interaction.guild.id] = []
            await interaction.followup.send(embed=Embed(title="Okay okay, chill bro!", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="Dude I'm litteraly not playing anything! You sutup!", color=Worpal.color))

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
