import discord
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from requests import get, post
from requests.exceptions import RequestException

from main import Worpal


@app_commands.guilds(discord.Object(940575531567546369), discord.Object(663825004256952342))
class Wynncraft(commands.GroupCog, name="wc"):
    def __init__(self, bot: Worpal):
        self.bot = bot
        self.url = "https://web-api.wynncraft.com/api/v3/"

    @app_commands.command(name="info", description="Get a player's info")
    async def info(self, interaction: Interaction, username: str):
        await interaction.response.defer()

        meta = self.get_wc_info(username.lower())
        if not meta:
            self.bot.logger.error("Error getting %s's info!", username)
            await interaction.followup.send(f"Error getting {username}'s info")
            return

        embed = Embed(
            title=f"{'[' + meta['shortenedRank'] + ']' if meta['shortenedRank'] is not None else ''} {username}'s info",
            color=meta['rank'])
        embed.set_thumbnail(url=meta['avatar'])
        embed.add_field(name="First joined", value=meta['firstJoin'][:10], inline=True)
        embed.add_field(name="Last joined", value=meta['lastJoin'][:10], inline=True)
        embed.add_field(name="Current status",
                        value=f"Online on {meta['location']['server']}" if meta['location']['online'] else "Offline",
                        inline=False)
        embed.add_field(name="Hours played", value=f"{meta['playtime']}", inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="avatar", description="Get the player's minecraft avatar")
    async def avatar(self, interaction: Interaction, username: str):
        await interaction.response.defer()
        avatar = self.get_avatar(username.lower())
        await interaction.followup.send(avatar if avatar else "Error getting avatar!")

    def get_avatar(self, username):
        if username in self.bot.mc_uuids:
            return f"https://minotar.net/avatar/{self.bot.mc_uuids[username]}"

        try:
            payload = [username]
            response = post(url="https://api.mojang.com/profiles/minecraft", json=payload).json()

            uuid = response[0]['id']

            self.bot.mc_uuids[username] = uuid
            return f"https://minotar.net/avatar/{uuid}"

        except RequestException:
            self.bot.logger.error("Error getting %s's avatar!", username)
            return False

    def get_wc_info(self, username: str):
        try:
            response = get(self.url + f"player/{username}").json()
            meta = response['meta']
            avatar = self.get_avatar(username)
            match meta['supportRank']:
                case 'VIP':
                    rank = 0x00aa00
                case 'VIP+':
                    rank = 0x55ffff
                case 'HERO':
                    rank = 0xff55ff
                case 'CHAMPION':
                    rank = 0xffaa00
                case _:
                    rank = 0x83c73d
            return {
                'avatar': avatar,
                'rank': rank,
                'shortenedRank': meta['shortenedRank'],
                'firstJoin': meta['firstJoin'][:10],
                'lastJoin': meta['lastJoin'][:10],
                'location': meta['location'],
                'playtime': meta['playtime']
            }
        except RequestException:
            self.bot.logger.error("Error getting %s's info!", username)
            return False


async def setup(bot):
    await bot.add_cog(Wynncraft(bot))
