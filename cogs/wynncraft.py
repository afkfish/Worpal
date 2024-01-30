import uuid

import discord
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from requests import get, post
from requests.exceptions import RequestException

from main import Worpal
from structures.player import Player


@app_commands.guilds(discord.Object(940575531567546369), discord.Object(663825004256952342))
class Wynncraft(commands.Cog):
    def __init__(self, bot: Worpal):
        self.bot = bot
        self.url = "https://api.wynncraft.com/v3"
        self.mojangAPI = "https://api.mojang.com/profiles/minecraft"

    def get_uuid(self, username: str) -> str:
        if username in self.bot.minecraft_uuid_cache:
            return str(self.bot.minecraft_uuid_cache[username])

        try:
            payload = [username]
            response = post(url=self.mojangAPI, json=payload)
            if response.ok:
                data = response.json()
                _uuid = uuid.UUID(data[0]['id'])
                self.bot.minecraft_uuid_cache[username] = _uuid

                return str(_uuid)

            raise RequestException

        except RequestException:
            self.bot.logger.error(f"Error getting UUID for {username}")
            raise RequestException

    def get_info(self, username: str) -> Player:
        try:
            _uuid = self.get_uuid(username)
            response = get(self.url + f"/player/{_uuid}")
            if response.ok:
                data = response.json()
                avatar = f"https://minotar.net/avatar/{_uuid}"
                return Player(data, _uuid, avatar)

            raise KeyError

        except RequestException | KeyError:
            self.bot.logger.error("Error getting %s's info!", username)
            raise RequestException

    @app_commands.command(name="wynn", description="Get a player's wynncraft info")
    async def info(self, interaction: Interaction, username: str):
        await interaction.response.defer()

        try:
            player = self.get_info(username.lower())
            await interaction.followup.send(embed=player.get_embed())

        except RequestException:
            self.bot.logger.error("Error getting %s's info!", username)
            await interaction.followup.send(f"Error getting {username}'s info")


async def setup(bot):
    await bot.add_cog(Wynncraft(bot))
