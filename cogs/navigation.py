from nextcord import slash_command, user_command, Embed, utils, Interaction
from nextcord.ext import commands

from cogs.play import slist, Play


class Navigation(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@slash_command(name="skip", description="Skip the current song")
	async def skip(self, ctx: Interaction):
		await ctx.response.defer()
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice is not None:
			voice.stop()
			await Play(commands.Cog).play_music(ctx)
			await ctx.followup.send(embed=Embed(title="Skipped :next_track:", color=self.bot.worp.color))
			return

		await ctx.followup.send(embed=Embed(title="I'm not playing anything", color=self.bot.worp.color))

	@user_command(name="Skip")
	async def skip_(self, ctx: Interaction, user):
		await self.skip(ctx)

	@slash_command(name="pause", description="Pause the song")
	async def pause_(self, ctx: Interaction):
		await ctx.response.defer()
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice.is_playing():
			voice.pause()
			await ctx.followup.send(embed=Embed(title="Paused :pause_button:", color=self.bot.worp.color))
			return

		await ctx.followup.send(embed=Embed(title="I'm not playing anything", color=self.bot.worp.color))

	@user_command(name="Pause")
	async def pause__(self, ctx: Interaction, user):
		await self.pause_(ctx)

	@slash_command(name="resume", description="Resume playing")
	async def resume_(self, ctx: Interaction):
		await ctx.response.defer()
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice.is_paused():
			voice.resume()
			await ctx.followup.send(embed=Embed(title="Resumed :arrow_forward:", color=self.bot.worp.color))
			return

		await ctx.followup.send(embed=Embed(title="Playing is not paused", color=self.bot.worp.color))

	@user_command(name="Resume")
	async def resume__(self, ctx: Interaction, user):
		await self.resume_(ctx)

	@slash_command(name="stop", description="Stop playing")
	async def stop_(self, ctx: Interaction):
		await ctx.response.defer()
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		voice.stop()
		self.bot.worp.music_queue[ctx.guild.id] = []
		await ctx.followup.send(embed=Embed(title="Stopped :stop_button:", color=self.bot.worp.color))

	@user_command(name="Stop")
	async def stop__(self, ctx: Interaction, user):
		await self.stop_(ctx)

	@slash_command(name="leave", description="Leave voice chat")
	async def leave_(self, ctx: Interaction):
		await ctx.response.defer(ephemeral=True)
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice is not None:
			await voice.disconnect()
			await ctx.followup.send(embed=Embed(title="Disconnected!", color=self.bot.worp.color), ephemeral=True)
			return

		await ctx.followup.send(embed=Embed(title="I'm not connected to a voice channel", color=self.bot.worp.color), ephemeral=True)

	@user_command(name="Leave")
	async def leave__(self, ctx: Interaction, user):
		await self.leave_(ctx)

	@slash_command(name="clear")
	async def clear(self, ctx: Interaction):
		pass

	@clear.subcommand(name="duplicates", description="Clear duplicated songs from queue.")
	async def clear_dup(self, ctx: Interaction):
		await ctx.response.defer()
		if self.bot.worp.music_queue[ctx.guild.id]:
			res = []
			[res.append(x) for x in self.bot.worp.music_queue[ctx.guild.id] if x not in res]
			self.bot.worp.music_queue[ctx.guild.id] = res
		embed = Embed(title="Duplicated songs cleared! :broom:", color=self.bot.worp.color)
		songs = slist(self.bot, ctx)
		if songs != "":
			embed.add_field(name="Songs: ", value=songs, inline=True)
		else:
			embed.add_field(name="Songs: ", value="No music in queue", inline=True)
		await ctx.followup.send(embed=embed)

	@clear.subcommand(name="all", description="Clear all songs from queue.")
	async def clear_all(self, ctx: Interaction):
		await ctx.response.defer()
		if self.bot.worp.music_queue[ctx.guild.id]:
			self.bot.worp.music_queue[ctx.guild.id] = []
		await ctx.followup.send(embed=Embed(title="Queue cleared! :broom:", color=self.bot.worp.color))


def setup(bot):
	bot.add_cog(Navigation(bot))
