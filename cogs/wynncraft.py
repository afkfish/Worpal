from nextcord import slash_command, SlashOption, Embed
from nextcord.ext import commands
from requests import get, post
from requests.exceptions import RequestException


class Wynncraft(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.url = "https://web-api.wynncraft.com/api/v3/"

	@slash_command(name="wc", description="Wynncraft parent command", guild_ids=[940575531567546369, 663825004256952342])
	async def wc(self, ctx):
		pass

	@wc.subcommand(name="info", description="Get a player's info")
	async def info(self, ctx,
				   username: str = SlashOption(name="username", description="The player's username", required=True)):
		await ctx.response.defer()

		meta = self.get_wc_info(username.lower())
		if not meta:
			await ctx.followup.send(f"Error getting {username}'s info")
			return

		embed = Embed(title=f"{'['+meta['shortenedRank']+']' if meta['shortenedRank'] is not None else ''} {username}'s info", color=meta['rank'])
		embed.set_thumbnail(url=meta['avatar'])
		embed.add_field(name="First joined", value=meta['firstJoin'][:10], inline=True)
		embed.add_field(name="Last joined", value=meta['lastJoin'][:10], inline=True)
		embed.add_field(name="Current status",
						value=f"Online on {meta['location']['server']}" if meta['location']['online'] else "Offline",
						inline=False)
		embed.add_field(name="Hours played", value=f"{meta['playtime']}", inline=False)

		await ctx.followup.send(embed=embed)

	@slash_command(name="avatar", description="Get the player's minecraft avatar", guild_ids=[940575531567546369])
	async def avatar(self, ctx,
					 username: str = SlashOption(name="username", description="The player's username", required=True)):
		await ctx.response.defer()
		avatar = self.get_avatar(username.lower())
		await ctx.followup.send(avatar if avatar is True else "Error getting avatar!")

	def get_avatar(self, username):
		if username in self.bot.mc_uuids:
			return f"https://minotar.net/avatar/{self.bot.mc_uuids[username]}"

		else:
			try:
				payload = [username]
				response = post(url="https://api.mojang.com/profiles/minecraft", json=payload).json()

				uuid = response[0]['id']

				self.bot.mc_uuids[username] = uuid
				return f"https://minotar.net/avatar/{uuid}"

			except RequestException:
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
			print(f"Error getting {username}'s info!")
			return False


def setup(bot):
	bot.add_cog(Wynncraft(bot))
