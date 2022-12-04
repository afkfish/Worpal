from nextcord import slash_command, Embed, utils
from nextcord.ext import commands

from cogs.play import slist, Play
from main import bot


class Navigation(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@slash_command(name="skip",
				   description="Skip the current song",
				   guild_ids=bot.guild_ids)
	async def skip(self, ctx):
		await ctx.response.defer()
		voice = utils.get(bot.voice_clients, guild=ctx.guild)
		if voice is not None:
			voice.stop()
			await Play(commands.Cog).play_music(ctx)
			embed = Embed(title="Skipped :next_track:")
			await ctx.followup.send(embed=embed)

	@slash_command(name="pause",
				   description="Pause the song",
				   guild_ids=bot.guild_ids)
	async def pause_(self, ctx):
		await ctx.response.defer()
		voice = utils.get(bot.voice_clients, guild=ctx.guild)
		if voice.is_playing():
			voice.pause()
			embed = Embed(title="Paused :pause_button:")
			await ctx.followup.send(embed=embed)

	@slash_command(name="resume",
				   description="Resume playing",
				   guild_ids=bot.guild_ids)
	async def resume_(self, ctx):
		await ctx.response.defer()
		voice = utils.get(bot.voice_clients, guild=ctx.guild)
		if voice.is_paused():
			voice.resume()
			embed = Embed(title="Resumed")
			await ctx.followup.send(embed=embed)

	@slash_command(name="stop",
				   description="Stop playing",
				   guild_ids=bot.guild_ids)
	async def stop_(self, ctx):
		await ctx.response.defer()
		voice = utils.get(bot.voice_clients, guild=ctx.guild)
		voice.stop()
		bot.music_queue[ctx.guild.id] = []
		embed = Embed(title="Stopped :stop_button:")
		await ctx.followup.send(embed=embed)

	@slash_command(name="leave",
				   description="Leave voice chat",
				   guild_ids=bot.guild_ids)
	async def leave_(self, ctx):
		await ctx.response.defer()
		voice = utils.get(bot.voice_clients, guild=ctx.guild)
		if voice is not None:
			await voice.disconnect()
			await ctx.followup.send(content="Disconnected!")

	@slash_command(name="clear",
				   guild_ids=bot.guild_ids)
	async def clear(self, ctx):
		pass

	@clear.subcommand(name="duplicates",
					  description="Clear duplicated songs from queue.")
	async def clear_dup(self, ctx):
		await ctx.response.defer()
		if bot.music_queue[ctx.guild.id]:
			res = []
			[res.append(x) for x in bot.music_queue[ctx.guild.id] if x not in res]
			bot.music_queue[ctx.guild.id] = res
		embed = Embed(title="Duplicated songs cleared! :broom:", color=0x152875)
		embed.set_author(name="Worpal", icon_url=bot.icon)
		songs = slist(ctx)
		if songs != "":
			embed.add_field(name="Songs: ", value=songs, inline=True)
		else:
			embed.add_field(name="Songs: ", value="No music in queue", inline=True)
		await ctx.followup.send(embed=embed)

	@clear.subcommand(name="all",
					  description="Clear all songs from queue.")
	async def clear_all(self, ctx):
		await ctx.response.defer()
		if bot.music_queue[ctx.guild.id]:
			bot.music_queue[ctx.guild.id] = []
		embed = Embed(title="Queue cleared! :broom:", color=0x152875)
		await ctx.followup.send(embed=embed)


def setup(bot):
	bot.add_cog(Navigation(bot))
