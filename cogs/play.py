import datetime as dt
import random
import re

from nextcord import *
from nextcord.ext import commands

from structures.track import Track
from structures.playlist import PlayList
from main import Worpal
from api.YouTubeAPI import get_link
from api.SpotifyAPI import SpotifyApi

JSON_FORMAT = {'name': '', 'songs': []}
FFMPEG_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"


async def process_query(bot: Worpal, ctx: Interaction, vc, playlist: PlayList):
	for track in playlist.tracks:
		track = get_link(track)
		playlist.tracks.pop(0)
		if track.is_valid():
			bot.music_queue[ctx.guild.id].append([track, vc])


def slist(bot: Worpal, ctx: Interaction) -> str:
	li = ""
	for track in bot.music_queue[ctx.guild.id]:
		li += track[0].title + "\n"
	return li


def announce_song(bot: Worpal, ctx: Interaction, view=None) -> None:
	track = bot.playing[ctx.guild.id][0]
	embed = Embed(title="Currently playing:", color=bot.color)
	embed.set_thumbnail(url=track.thumbnail)
	playtime = dt.timedelta(seconds=(dt.datetime.utcnow() - bot.playing[ctx.guild.id][0].start).seconds)
	embed.add_field(name=track.title, value=f"Currently at:\n{playtime}", inline=True)
	embed.set_footer(text=str(dt.timedelta(seconds=int(track.duration))))

	if view is not None:
		bot.loop.create_task(ctx.followup.send(embed=embed, view=view))
	else:
		bot.loop.create_task(ctx.followup.send(embed=embed))


class Navigation(ui.View):
	def __init__(self, bot: Worpal):
		super().__init__(timeout=50)
		self.bot = bot

	@ui.button(emoji="🔄", style=ButtonStyle.red, disabled=True)
	async def replay(self, button: ui.Button, ctx: Interaction):
		self.stop()
		for child in self.children:
			child.disabled = True
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		voice: VoiceClient = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice is not None and isinstance(voice, VoiceClient):
			self.bot.music_queue[ctx.guild.id].insert(0, self.bot.playing[ctx.guild.id])
			voice.stop()
			await Play(self.bot).play_music(ctx)
			embed = Embed(title="Replaying 🔄")
			await ctx.send(embed=embed)

	@ui.button(emoji="▶️", style=ButtonStyle.grey)
	async def resume(self, button: ui.Button, ctx: Interaction):
		self.stop()
		for child in self.children:
			child.disabled = True
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		voice: VoiceClient = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if isinstance(voice, VoiceClient) and voice.is_paused():
			voice.resume()
			embed = Embed(title="Resumed ▶️")
			await ctx.send(embed=embed)

	@ui.button(emoji="⏸️", style=ButtonStyle.grey)
	async def pause(self, button: ui.Button, ctx: Interaction):
		self.stop()
		for child in self.children:
			child.disabled = True
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		voice: VoiceClient = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if isinstance(voice, VoiceClient) and voice.is_playing():
			voice.pause()
			embed = Embed(title="Paused ⏸️")
			await ctx.send(embed=embed)

	@ui.button(emoji="⏭️", style=ButtonStyle.grey)
	async def skip(self, button: ui.Button, ctx: Interaction):
		self.stop()
		for child in self.children:
			child.disabled = True
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		voice: VoiceClient = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice is not None and isinstance(voice, VoiceClient):
			voice.stop()
			await Play(self.bot).play_music(ctx)
			embed = Embed(title="Skipped ⏭️")
			await ctx.send(embed=embed)


class Play(commands.Cog):

	def __init__(self, bot: Worpal):
		self.bot = bot

	def play_next(self, ctx: Interaction):
		if len(self.bot.music_queue[ctx.guild.id]) == 0:
			return

		vc: VoiceClient = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if vc is None or not isinstance(vc, VoiceClient):
			return

		if vc.is_playing():
			return

		if self.bot.looping(ctx.guild.id):
			m_url = self.bot.playing[ctx.guild.id][0].source

		elif self.bot.shuffle(ctx.guild.id):
			entry = random.choice(self.bot.music_queue[ctx.guild.id])
			m_url = entry[0].source
			self.bot.playing[ctx.guild.id] = entry[0]
			self.bot.music_queue[ctx.guild.id].remove(entry)

		else:
			m_url = self.bot.music_queue[ctx.guild.id][0][0].source
			self.bot.playing[ctx.guild.id] = self.bot.music_queue[ctx.guild.id][0]
			self.bot.music_queue[ctx.guild.id].pop(0)

		if self.bot.announce(ctx.guild.id):
			announce_song(self.bot, ctx)

		vc.play(FFmpegPCMAudio(source=m_url, before_options=FFMPEG_OPTIONS), after=self.play_next(ctx))
		self.bot.playing[ctx.guild.id][0].start = dt.datetime.utcnow()

	async def play_music(self, ctx: Interaction):
		if len(self.bot.music_queue[ctx.guild.id]) == 0:
			return

		m_url = self.bot.music_queue[ctx.guild.id][0][0].source
		vc: VoiceClient = utils.get(self.bot.voice_clients, guild=ctx.guild)

		if vc is None or not isinstance(vc, VoiceClient):
			vc = await self.bot.music_queue[ctx.guild.id][0][1].connect()

		elif vc.channel != self.bot.music_queue[ctx.guild.id][0][1]:
			await vc.move_to(self.bot.music_queue[ctx.guild.id][0][1])

		if vc.is_playing():
			return

		self.bot.playing[ctx.guild.id] = self.bot.music_queue[ctx.guild.id][0]
		self.bot.music_queue[ctx.guild.id].pop(0)

		if self.bot.announce(ctx.guild.id):
			announce_song(self.bot, ctx)

		vc.play(FFmpegPCMAudio(source=m_url, before_options=FFMPEG_OPTIONS), after=self.play_next(ctx))
		self.bot.playing[ctx.guild.id][0].start = dt.datetime.utcnow()

	@slash_command(name="play", description="Play a song")
	async def play(self, ctx: Interaction,
				   query: str = SlashOption(name="music", description="the music to be played", required=True)):
		await ctx.response.defer()

		if not ctx.user.voice:
			await ctx.followup.send(content="Connect to a voice channel!", ephemeral=True)
			return

		track = Track(query=query, user=ctx.user, spotify=True if "spotify" in query else False)

		voice_channel = ctx.user.voice.channel
		if "open.spotify.com" not in query:
			track = get_link(track)
			if not track.is_valid():
				await ctx.followup.send(content="Couldn't play the song.", ephemeral=True)
				return

			self.bot.music_queue[ctx.guild.id].append([track, voice_channel])
			await ctx.followup.send(embed=track.get_embed())
			await self.play_music(ctx)
			return

		playlist = None
		if "/track" in query:
			# https://open.spotify.com/track/5oKRyAx215xIycigG6NNwt?si=834b843759b84497
			# https://open.spotify.com/track/2Oz3Tj8RbLBZFW5Adsyzyj?si=ae09611876c44d65
			track_id = re.search(r"track/(.+?)\?si", query).group(1)
			track.id = track_id
			track = SpotifyApi().get_by_id(track=track)

		elif "/playlist" in query:
			playlist_id = re.search(r"playlist/(.+?)\?si", query).group(1)
			playlist = SpotifyApi().get_playlist(playlist_id=playlist_id)

			ctx.followup.send(embed=playlist.get_embed())
			track = playlist.tracks[0]

		track = get_link(track)
		if not track.is_valid():
			await ctx.followup.send(content="Couldn't play the song.", ephemeral=True)
			return

		self.bot.music_queue[ctx.guild.id].append([track, voice_channel])
		await ctx.followup.send(embed=track.get_embed() if playlist is None else playlist.get_embed())
		await self.play_music(ctx)

		if playlist is not None:
			await process_query(self.bot, ctx, voice_channel, playlist)

	@slash_command(name="queue", description="Displays the songs in the queue")
	async def queue(self, ctx: Interaction):
		await ctx.response.defer()
		embed = Embed(title="Queue", color=self.bot.color)
		songs = slist(self.bot, ctx)
		if songs:
			embed.add_field(name="Songs: ", value=songs, inline=True)
		else:
			embed.add_field(name="Songs: ", value="No music in queue", inline=True)
		await ctx.followup.send(embed=embed)

	@slash_command(name="playskip", description="Skip the current song and play the given one.")
	async def playskip(self, ctx: Interaction, query: str = SlashOption(name="music",
														   description="the music to be played",
														   required=True)):
		await ctx.response.defer()
		if not ctx.user.voice:
			await ctx.followup.send(content="Connect to a voice channel!")
			return

		# embed = Embed(title="Playing " + f"from Spotify {bot.get_emoji(944554099175727124)}" if "spotify" in music else "",
		# 			  color=bot.color)
		voice: VoiceClient = utils.get(self.bot.voice_clients, guild=ctx.guild)
		voice_channel = ctx.user.voice.channel
		if voice is None and not isinstance(voice, VoiceClient):
			await ctx.followup.send(content="Bot is not connected! Try playing a song first.", ephemeral=True)
			return

		voice.stop()
		track = Track(query=query, user=ctx.user)
		track = get_link(track)

		if not track.is_valid():
			await ctx.followup.send(content="Couldn't play the song.", ephemeral=True)
			return

		self.bot.music_queue[ctx.guild.id].insert(0, [track, voice_channel])
		await ctx.followup.send(embed=track.get_embed())
		await self.play_music(ctx)

	@slash_command(name="np", description="The song that is currently being played")
	async def np(self, ctx: Interaction):
		await ctx.response.defer()
		if len(self.bot.playing[ctx.guild.id]) > 0:
			view = Navigation(self.bot)
			announce_song(self.bot, ctx, view)
			await view.wait()

		else:
			await ctx.followup.send(content="No song has been played yet!", ephemeral=True)


# @slash_command(name="createpl",
# 			   description="Create playlists",
# 			   guild_ids=[940575531567546369])
# async def createplaylist(self, ctx, name: str = SlashOption(name="name",
# 															description="playlist name",
# 															required=True)):
# 	JSON_FORMAT['name'] = name
# 	with open("./playlists/{}.json".format(name), "w") as f:
# 		json.dump(JSON_FORMAT, f, indent=4)
# 	f.close()
# 	await ctx.response.send_message("Playlis {} was succefully created".format(name))
#
# @slash_command(name="addsong",
# 			   description="Append a song to existing playlists",
# 			   guild_ids=[940575531567546369])
# async def addsong(self, ctx,
# 				  playlist: str = SlashOption(name="playlist",
# 											  description="the destination playlist",
# 											  required=True),
# 				  song: str = SlashOption(name="song",
# 										  description="the song's URL",
# 										  required=True)):
# 	with open("./playlists/{}.json".format(playlist), "r") as a:
# 		data = json.load(a)
# 	data['songs'].append(song)
# 	with open("./playlists/{}.json".format(playlist), "w") as f:
# 		json.dump(data, f, indent=4)
# 	await ctx.response.send_message("Song was successfully added!")
#
# @slash_command(name="playlist",
# 			   description="Play songs from a playlist",
# 			   guild_ids=[940575531567546369])
# async def playlist(self, ctx, playlist_name: str = SlashOption(name="playlist_name",
# 															   description="the name of the playlist",
# 															   required=True)):
# 	with open("./playlists/{}.json".format(playlist_name), "r") as f:
# 		data = json.load(f)
# 	for item in data['songs']:
# 		vc = api.get(bot.voice_clients, guild=ctx.guild)
# 		voice_channel = ctx.user.voice.channel
# 		if voice_channel is None:
# 			await ctx.response.send_message("Connect to a voice channel!")
# 		else:
# 			song = fast_link(item)
# 			if song is False:
# 				await ctx.response.send_message("Could not play the song from the playlist.")
# 			else:
# 				bot.music_queue.append([song, voice_channel])
# 				await self.play_music(ctx)
# 	await ctx.response.send_message("Playlist succefully loaded!")

# still in beta and not working properly
# @slash_command(name="lyrics",
# 			   description="test",
# 			   guild_ids=[940575531567546369])
# async def lyrics(self, ctx):
# 	await ctx.response.defer()
# 	embed = Embed(title="Song Lyrics:", color=bot.color)
# 	
# 	try:
# 		song = GeniusApi().get_song(bot.playing[ctx.guild.id][0]['title'])
# 		lyrics = get_lyrics(song)
# 		ly = []
# 		for i in range(round(len(lyrics) / 1024) - 1):
# 			ly.append(lyrics[i:i + 1024])
# 		embed.add_field(name=song["title"], value=embeds.EmptyEmbed)
# 		embed.set_thumbnail(url=bot.playing[ctx.guild.id][0]['thumbnail'])
# 		print(ly)
# 		print(len(ly))
# 		embedl = [embed]
# 		for block in ly:
# 			nembed = Embed(title=embeds.EmptyEmbed, color=bot.color)
# 			nembed.add_field(name=embeds.EmptyEmbed, value=block)
# 			embedl.append(nembed)
# 		print(embedl)
# 		await ctx.followup.send(embeds=embedl[:10])
# 	except IndexError as ex:
# 		print(f"{type(ex).__name__} {ex}")
# 		await ctx.followup.send(content=f"Error: {ex}")


def setup(bot):
	bot.add_cog(Play(bot))
