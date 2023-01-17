import datetime as dt

from nextcord import slash_command, FFmpegPCMAudio, utils
from nextcord.ext import commands

from cogs.play import Play
from main import bot


class Seek(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@slash_command(name='seek', description='Seek to a specific time in the song.')
	async def seek(self, ctx, time):
		await ctx.response.defer()

		voice_channel = ctx.user.voice.channel
		voice = utils.get(bot.voice_clients, guild=ctx.guild)

		if len(bot.playing[ctx.guild.id]) == 0:
			await ctx.followup.send(content='You need to play a song before you can seek in it.')
			return

		m_url = bot.playing[ctx.guild.id][0].source

		if voice_channel is None:
			await ctx.followup.send(content='You need to be in a voice channel to use this command.')
			return

		if voice == "" or voice is None:
			voice = await bot.playing[ctx.guild.id][1].connect()

		elif voice.channel != bot.playing[ctx.guild.id][1]:
			await voice.move_to(bot.playing[ctx.guild.id][1])

		formatted_time = dt.timedelta(seconds=int(time))
		voice.stop()
		# play the song with discord.FFmpegPCMaudio
		voice.play(
			FFmpegPCMAudio(before_options=f'-ss {time} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
						   source=m_url),
			after=Play(commands.Cog).play_next(ctx))
		bot.playing[ctx.guild.id][-1] = dt.datetime.utcnow() - dt.timedelta(seconds=int(time))
		# send a message saying the bot is now playing the song
		await ctx.followup.send(
			content=f'Now playing {bot.playing[ctx.guild.id][0].title} from {formatted_time} seconds.')


# add the cog to the bot
def setup(bot):
	bot.add_cog(Seek(bot))
