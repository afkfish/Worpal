from nextcord import Embed, slash_command
from nextcord.ext import commands

import main


class Help(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@staticmethod
	async def help_embed(ctx, command: str):
		await ctx.response.defer()
		embed = Embed(color=0x152875)
		embed.set_author(name="Worpal", icon_url=main.icon)
		match command:
			case "play":
				embed.title = "Play :arrow_forward:"
				embed.add_field(name="Usage:", value="The play command accepts words, youtube links, spotify links to "
													 "songs and playlists (only the first 10 song will be added from "
													 "them to the queue) as an argument. "
													 "The user must be in a voice channel when executing the command! "
													 "The bot cannot play livestreams and videos that are age "
													 "restricted! "
													 "The bot will search for a video named as the argument or the "
													 "link, or in case of a spotify link then on spotify and "
													 "try to stream it into the voice channel where the user is "
													 "present.")
			case "queue":
				embed.title = "Queue"
				embed.add_field(name="Usage:", value="The queue command sends an embed displaying the previously "
													 "added tracks that will be played.")
			case "skip":
				embed.title = "Skip :next_track:"
				embed.add_field(name="Usage:", value="The skip command allows the user to skip a track when the bot "
													 "is playing. If nothing is in the queue then the bot will stop.")
			case "pause":
				embed.title = "Pause :pause_button:"
				embed.add_field(name="Usage:", value="The pause command has no parameters. It tries to stop the music "
													 "if the bot is playing.")
			case "resume":
				embed.title = "Resume"
				embed.add_field(name="Usage:", value="The resume command resumes the music if it has been paused.")
			case "stop":
				embed.title = "Stop :stop_button:"
				embed.add_field(name="Usage:", value="The stop command stops the media playing and clears the queue. "
													 "The next song in the queue can be played once a new song is "
													 "added by a play command.")
			case "leave":
				embed.title = "Leave"
				embed.add_field(name="Usage:", value="The leave command disconnects the bot from the voice channel if "
													 "it was in one.")
			case "clear duplicates":
				embed.title = "Clear duplicates"
				embed.add_field(name="Usage:", value="The clear duplicates command removes the duplicated songs from "
													 "the queue if there are any.")
			case "clear all":
				embed.title = "Clear all"
				embed.add_field(name="Usage:", value="The clear all command empties the queue completely.")
			case "np":
				embed.title = "Now Playing"
				embed.add_field(name="Usage:", value="The np command sends an embed representing the music that is "
													 "currently being played. If the music stopped or skipped but the "
													 "queue is empty than the previously played song will be sent.")
			case "lyrics":
				embed.title = "Lyrics"
				embed.add_field(name="Usage:", value="The lyrics command tries to find the song on genius and sends "
													 "back the lyrics if it succeded. Not every song will 100% have a "
													 "lyric. If you are sure it has but it is not available on genius "
													 "than the subtitle command could help.")
			case "ping":
				embed.title = "Ping"
				embed.add_field(name="Usage:", value="The ping command measures the latency from the server to the "
													 "client in miliseconds.")
			case _:
				pass
		await ctx.followup.send(embed=embed)

	@slash_command(name="help", description="Get info on commands.", guild_ids=main.bot.guild_ids)
	async def help(self, ctx):
		pass

	@help.subcommand(name="play", description="play command")
	async def help_play(self, ctx):
		await self.help_embed(ctx=ctx, command="play")

	@help.subcommand(name="queue", description="queue command")
	async def help_queue(self, ctx):
		await self.help_embed(ctx=ctx, command="queue")

	@help.subcommand(name="skip", description="skip command")
	async def help_skip(self, ctx):
		await self.help_embed(ctx=ctx, command="skip")

	@help.subcommand(name="pause", description="pause command")
	async def help_pause(self, ctx):
		await self.help_embed(ctx=ctx, command="pause")

	@help.subcommand(name="resume", description="resume command")
	async def help_resume(self, ctx):
		await self.help_embed(ctx=ctx, command="resume")

	@help.subcommand(name="stop", description="stop command")
	async def help_stop(self, ctx):
		await self.help_embed(ctx=ctx, command="stop")

	@help.subcommand(name="leave", description="leave command")
	async def help_leave(self, ctx):
		await self.help_embed(ctx=ctx, command="leave")

	@help.subcommand(name="clear_dumplicates", description="clear duplicates command")
	async def help_clear_d(self, ctx):
		await self.help_embed(ctx=ctx, command="clear duplicates")

	@help.subcommand(name="clear_all", description="clear all command")
	async def help_clear_a(self, ctx):
		await self.help_embed(ctx=ctx, command="clear all")

	@help.subcommand(name="np", description="np command")
	async def help_np(self, ctx):
		await self.help_embed(ctx=ctx, command="np")

	# @help.subcommand(name="lyrics", description="lyrics command")
	# async def help_lyrics(self, ctx):
	#     await self.help_embed(ctx=ctx, command="lyrics")

	@help.subcommand(name="ping", description="ping command")
	async def help_ping(self, ctx):
		await self.help_embed(ctx=ctx, command="ping")


def setup(bot):
	bot.add_cog(Help(bot))
