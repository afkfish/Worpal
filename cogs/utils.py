import discord
from discord import app_commands, Interaction
from discord.ext import commands

from main import Worpal


@app_commands.guilds(discord.Object(str(940575531567546369)))
class Debug(commands.Cog):
    def __init__(self, bot: Worpal):
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction: Interaction):
        await interaction.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms")


async def setup(bot):
    await bot.add_cog(Debug(bot))
