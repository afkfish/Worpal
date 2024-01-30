import os
import sys

import discord
from discord import app_commands, Interaction, VoiceClient
from discord.ext import commands

from main import Worpal


@app_commands.guilds(discord.Object(663825004256952342), discord.Object(940575531567546369))
class Debug(commands.Cog):
    def __init__(self, bot: Worpal):
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction: Interaction):
        await interaction.response().send_message(f"Pong! {round(self.bot.latency * 1000)}ms")

    @app_commands.command()
    async def reload(self, interaction: Interaction):
        await interaction.response().send_message("Reloading in 5s!")
        vc: VoiceClient = interaction.guild.voice_client
        if vc:
            await vc.disconnect(force=True)

        os.execv(sys.executable, ["python3"] + ["restart.py"])


async def setup(bot):
    await bot.add_cog(Debug(bot))
