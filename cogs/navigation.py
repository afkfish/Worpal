from discord import app_commands, Interaction, VoiceClient, Embed
from discord.ext import commands

from cogs.play import slist, Play
from main import Worpal


class Navigation(commands.Cog):

    def __init__(self, bot: Worpal):
        self.bot = bot

    # @app_commands.context_menu(name="Skip")
    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: Interaction):
        await interaction.response.defer()
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            voice.stop()
            await Play(self.bot).play_music(interaction)
            await interaction.followup.send(embed=Embed(title="Skipped :next_track:", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="I'm not playing anything", color=Worpal.color))

    # @app_commands.(name="Skip")
    # async def skip_(self, interaction: Interaction, user):
    #     await self.skip(interaction)

    # @app_commands.context_menu(name="Pause")
    @app_commands.command(name="pause", description="Pause the song")
    async def pause(self, interaction: Interaction):
        await interaction.response.defer()
        voice: VoiceClient = interaction.guild.voice_client
        if voice and voice.is_playing():
            voice.pause()
            await interaction.followup.send(embed=Embed(title="Paused :pause_button:", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="I'm not playing anything", color=Worpal.color))

    # @user_command(name="Pause")
    # async def pause_(self, interaction: Interaction, user):
    #     await self.pause(interaction)

    # @app_commands.context_menu(name="Resume")
    @app_commands.command(name="resume", description="Resume playing")
    async def resume(self, interaction: Interaction):
        await interaction.response.defer()
        voice: VoiceClient = interaction.guild.voice_client
        if voice and voice.is_paused():
            voice.resume()
            await interaction.followup.send(embed=Embed(title="Resumed :arrow_forward:", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="Playing is not paused", color=Worpal.color))

    # @user_command(name="Resume")
    # async def resume_(self, interaction: Interaction, user):
    #     await self.resume(interaction)

    # @app_commands.context_menu(name="Resume")
    @app_commands.command(name="stop", description="Stop playing")
    async def stop(self, interaction: Interaction):
        await interaction.response.defer()
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            voice.stop()
            self.bot.music_queue[interaction.guild.id] = []
            await interaction.followup.send(embed=Embed(title="Stopped :stop_button:", color=Worpal.color))
            return

        await interaction.followup.send(embed=Embed(title="Error!", color=Worpal.color))

    # @user_command(name="Stop")
    # async def stop_(self, interaction: Interaction, user):
    #     await self.stop(interaction)

    # @app_commands.context_menu(name="Leave")
    @app_commands.command(name="leave", description="Leave voice chat")
    async def leave(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            await voice.disconnect()
            await interaction.followup.send(embed=Embed(title="Disconnected!", color=Worpal.color), ephemeral=True)
            return

        await interaction.followup.send(embed=Embed(title="I'm not connected to a voice channel", color=Worpal.color), ephemeral=True)

    # async def leave_(self, interaction: Interaction):
    #     await self.leave(interaction)

    group = app_commands.Group(name="clear", description="...")

    @group.command(name="duplicates", description="Clear duplicated songs from queue.")
    async def clear_dup(self, interaction: Interaction):
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

    @group.command(name="all", description="Clear all songs from queue.")
    async def clear_all(self, interaction: Interaction):
        await interaction.response.defer()
        if self.bot.music_queue[interaction.guild.id]:
            self.bot.music_queue[interaction.guild.id] = []

        await interaction.followup.send(embed=Embed(title="Queue cleared! :broom:", color=Worpal.color))


async def setup(bot):
    await bot.add_cog(Navigation(bot))
