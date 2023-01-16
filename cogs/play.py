import datetime as dt
import random
import re

from nextcord import Embed, utils, SlashOption, slash_command, FFmpegPCMAudio, ui, ButtonStyle
from nextcord.ext import commands

from main import bot_loop, bot_announce, bot_shuffle
from utils.song_info import fast_link
from utils.spotify_api_request import SpotifyApi

JSON_FORMAT = {'name': '', 'songs': []}
FFMPEG_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"


async def process_query(bot, ctx, vc):
	for entry in bot.query[ctx.guild.id]:
		track = fast_link(entry)
		bot.query[ctx.guild.id].pop(0)
		if track:
			bot.music_queue[ctx.guild.id].append([track, vc])


def slist(bot, ctx):
	li = ""
	for song in bot.music_queue[ctx.guild.id]:
		li += song[0]['title'] + "\n"
	return li


def announce_song(bot, ctx, view=None):
	a = bot.playing[ctx.guild.id]
	embed = Embed(title="Currently playing:", color=bot.color)
	embed.set_author(name="Worpal", icon_url=bot.icon)
	embed.set_thumbnail(url=a[0]['thumbnail'])
	if len(bot.playing[ctx.guild.id]) > 2:
		timedelta = (dt.datetime.utcnow() - bot.playing[ctx.guild.id][-1]).seconds
		playtime = dt.timedelta(seconds=timedelta)
		embed.add_field(name=a[0]['title'], value=f"Currently at:\n{playtime}", inline=True)
		embed.set_footer(text=str(dt.timedelta(seconds=int(a[0]['duration']))))
	else:
		embed.add_field(name=a[0]['title'], value=f"Lenght:\n{str(dt.timedelta(seconds=int(a[0]['duration'])))}",
						inline=True)
	if view is not None:
		bot.loop.create_task(ctx.followup.send(embed=embed, view=view))
	else:
		bot.loop.create_task(ctx.followup.send(embed=embed))


class Navigation(ui.View):
	def __init__(self, bot):
		super().__init__(timeout=10)
		self.bot = bot

	@ui.button(emoji="🔄", style=ButtonStyle.red, disabled=True)
	async def replay(self, button: ui.Button, ctx):
		self.stop()
		for child in self.children:
			child.disabled = True
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice is not None:
			self.bot.music_queue[ctx.guild.id].insert(0, self.bot.playing[ctx.guild.id])
			voice.stop()
			await Play(commands.Cog).play_music(ctx)
			embed = Embed(title="Replaying 🔄")
			await ctx.send(embed=embed)

	@ui.button(emoji="▶️", style=ButtonStyle.grey)
	async def resume(self, button: ui.Button, ctx):
		self.stop()
		for child in self.children:
			child.disabled = True
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice.is_paused():
			voice.resume()
			embed = Embed(title="Resumed ▶️")
			await ctx.send(embed=embed)

	@ui.button(emoji="⏸️", style=ButtonStyle.grey)
	async def pause(self, button: ui.Button, ctx):
		self.stop()
		for child in self.children:
			child.disabled = True
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice.is_playing():
			voice.pause()
			embed = Embed(title="Paused ⏸️")
			await ctx.send(embed=embed)

	@ui.button(emoji="⏭️", style=ButtonStyle.grey)
	async def skip(self, button: ui.Button, ctx):
		self.stop()
		for child in self.children:
			child.disabled = True
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if voice is not None:
			voice.stop()
			await Play(commands.Cog).play_music(ctx)
			embed = Embed(title="Skipped ⏭️")
			await ctx.send(embed=embed)


class Play(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	def play_next(self, ctx):
		if len(self.bot.music_queue[ctx.guild.id]) == 0:
			return

		vc = utils.get(self.bot.voice_clients, guild=ctx.guild)
		if vc is None:
			return

		if vc.is_playing():
			return

		m_url = ""
		if bot_loop(ctx.guild.id):
			m_url = self.bot.playing[ctx.guild.id][0]['source']

		elif bot_shuffle(ctx.guild.id):
			song = random.choice(self.bot.music_queue[ctx.guild.id])
			m_url = song[0]['source']
			self.bot.playing[ctx.guild.id] = song
			self.bot.music_queue[ctx.guild.id].remove(song)

		else:
			m_url = self.bot.music_queue[ctx.guild.id][0][0]['source']
			self.bot.playing[ctx.guild.id] = self.bot.music_queue[ctx.guild.id][0]
			self.bot.music_queue[ctx.guild.id].pop(0)

		if bot_announce(ctx.guild.id):
			announce_song(self.bot, ctx)

		vc.play(FFmpegPCMAudio(source=m_url, before_options=FFMPEG_OPTIONS), after=self.play_next(ctx))
		self.bot.playing[ctx.guild.id].append(dt.datetime.utcnow())

	async def play_music(self, ctx):
		if len(self.bot.music_queue[ctx.guild.id]) == 0:
			return

		m_url = self.bot.music_queue[ctx.guild.id][0][0]['source']
		vc = utils.get(self.bot.voice_clients, guild=ctx.guild)

		if vc is None:
			vc = await self.bot.music_queue[ctx.guild.id][0][1].connect()

		elif vc.channel != self.bot.music_queue[ctx.guild.id][0][1]:
			await vc.move_to(self.bot.music_queue[ctx.guild.id][0][1])

		if vc.is_playing():
			return

		self.bot.playing[ctx.guild.id] = self.bot.music_queue[ctx.guild.id][0]
		self.bot.music_queue[ctx.guild.id].pop(0)

		if bot_announce(ctx.guild.id):
			announce_song(self.bot, ctx)

		vc.play(FFmpegPCMAudio(source=m_url, before_options=FFMPEG_OPTIONS), after=self.play_next(ctx))
		self.bot.playing[ctx.guild.id].append(dt.datetime.utcnow())

	@slash_command(name="play", description="Play a song")
	async def play(self, ctx,
				   music: str = SlashOption(name="music", description="the music to be played", required=True)):
		await ctx.response.defer()

		if not ctx.user.voice:
			await ctx.followup.send(content="Connect to a voice channel!", ephemeral=True)
			return

		embed = Embed(title="Song added to queue" + (
			f" from Spotify {self.bot.get_emoji(944554099175727124)}" if "spotify" in music else ""
		), color=self.bot.color)

		voice_channel = ctx.user.voice.channel
		if "open.spotify.com" not in music:
			song = fast_link(music)
			if not song:
				await ctx.followup.send(content="Couldn't play the song.", ephemeral=True)
				return

			self.bot.music_queue[ctx.guild.id].append([song, voice_channel])
			embed.set_thumbnail(url=self.bot.music_queue[ctx.guild.id][-1][0]['thumbnail'])
			embed.add_field(name=self.bot.music_queue[ctx.guild.id][-1][0]['title'],
							value=f"{str(dt.timedelta(seconds=int(self.bot.music_queue[ctx.guild.id][-1][0]['duration'])))}",
							inline=True)
			embed.set_footer(text="Song requested by: " + ctx.user.name)
			await ctx.followup.send(embed=embed)
			await self.play_music(ctx)
			return

		if "/track" in music:
			# https://open.spotify.com/track/5oKRyAx215xIycigG6NNwt?si=834b843759b84497
			# https://open.spotify.com/track/2Oz3Tj8RbLBZFW5Adsyzyj?si=ae09611876c44d65
			a = re.search(r"track/(.+?)\?si", music).group(1)
			song = SpotifyApi().get_by_id(trackid=a)
			artists = ""
			for artist in song['album']['artists']:
				artists += "".join(f"{artist['name']}, ")
			artists = artists[:-2]
			embed.set_thumbnail(url=song['album']['images'][0]['url'])
			embed.add_field(name=f"{song['name']}\n\n",
							value=f"{artists}\n"
								  f"{str(dt.timedelta(seconds=song['duration_ms']))}")
			self.bot.query[ctx.guild.id].append(f"{song['name']}\t{artists}")

		elif "/playlist" in music:
			a = re.search(r"playlist/(.+?)\?si", music).group(1)
			playlist = SpotifyApi().get_playlist(playlist_id=a)
			for i in range(10):
				song = playlist['tracks']['items'][i]
				artists = []
				for artist in song['track']['artists']:
					artists.append(artist['name'])
				self.bot.query[ctx.guild.id].append(f"{song['track']['name']}\t{', '.join(artists)}")
			embed.title = f"Playlist added to queue from Spotify {self.bot.get_emoji(944554099175727124)}"
			embed.set_thumbnail(url=playlist['images'][0]['url'])
			embed.add_field(name=f"{playlist['name']}\n\n",
							value=f"{playlist['owner']['display_name']}\n")

		embed.set_footer(text="Song requested by: " + ctx.user.name)
		if len(self.bot.query) > 0:
			track = fast_link(self.bot.query[ctx.guild.id][0])

		if not track:
			await ctx.followup.send(content="Couldn't play the song.", ephemeral=True)
			self.bot.query[ctx.guild.id].pop(0)
			return

		self.bot.music_queue[ctx.guild.id].append([track, voice_channel])
		await ctx.followup.send(embed=embed)
		await self.play_music(ctx)

		if len(self.bot.query[ctx.guild.id]) > 0:
			await process_query(self.bot, ctx, voice_channel)

	@slash_command(name="queue", description="Displays the songs in the queue")
	async def queue(self, ctx):
		await ctx.response.defer()
		embed = Embed(title="Queue", color=self.bot.color)
		songs = slist(self.bot, ctx)
		if songs:
			embed.add_field(name="Songs: ", value=songs, inline=True)
		else:
			embed.add_field(name="Songs: ", value="No music in queue", inline=True)
		await ctx.followup.send(embed=embed)

	@slash_command(name="playskip", description="Skip the current song and play the given one.")
	async def playskip(self, ctx, music: str = SlashOption(name="music",
														   description="the music to be played",
														   required=True)):
		await ctx.response.defer()
		if not ctx.user.voice:
			await ctx.followup.send(content="Connect to a voice channel!")
			return

		embed = Embed(title="Playing " + f"from Spotify {self.bot.get_emoji(944554099175727124)}" if "spotify" in music else "",
					  color=self.bot.color)
		voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
		voice_channel = ctx.user.voice.channel
		if voice is None:
			await ctx.followup.send(content="Bot is not connected! Try playing a song first.", ephemeral=True)
			return

		voice.stop()
		song = fast_link(music)

		if not song:
			await ctx.followup.send(content="Couldn't play the song.", ephemeral=True)
			return

		self.bot.music_queue[ctx.guild.id].insert(0, [song, voice_channel])
		embed.set_thumbnail(url=self.bot.music_queue[ctx.guild.id][0][0]['thumbnail'])
		embed.add_field(name=self.bot.music_queue[ctx.guild.id][0][0]['title'],
						value=f"{str(dt.timedelta(seconds=int(self.bot.music_queue[ctx.guild.id][-1][0]['duration'])))}",
						inline=True)
		embed.set_footer(text="Song requested by: " + ctx.user.name)
		await ctx.followup.send(embed=embed)
		await self.play_music(ctx)

	@slash_command(name="np", description="The song that is currently being played")
	async def np(self, ctx):
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
# 		vc = utils.get(self.bot.voice_clients, guild=ctx.guild)
# 		voice_channel = ctx.user.voice.channel
# 		if voice_channel is None:
# 			await ctx.response.send_message("Connect to a voice channel!")
# 		else:
# 			song = fast_link(item)
# 			if song is False:
# 				await ctx.response.send_message("Could not play the song from the playlist.")
# 			else:
# 				self.bot.music_queue.append([song, voice_channel])
# 				await self.play_music(ctx)
# 	await ctx.response.send_message("Playlist succefully loaded!")

# still in beta and not working properly
# @slash_command(name="lyrics",
# 			   description="test",
# 			   guild_ids=[940575531567546369])
# async def lyrics(self, ctx):
# 	await ctx.response.defer()
# 	embed = Embed(title="Song Lyrics:", color=self.bot.color)
# 	
# 	try:
# 		song = GeniusApi().get_song(self.bot.playing[ctx.guild.id][0]['title'])
# 		lyrics = get_lyrics(song)
# 		ly = []
# 		for i in range(round(len(lyrics) / 1024) - 1):
# 			ly.append(lyrics[i:i + 1024])
# 		embed.add_field(name=song["title"], value=embeds.EmptyEmbed)
# 		embed.set_thumbnail(url=self.bot.playing[ctx.guild.id][0]['thumbnail'])
# 		print(ly)
# 		print(len(ly))
# 		embedl = [embed]
# 		for block in ly:
# 			nembed = Embed(title=embeds.EmptyEmbed, color=self.bot.color)
# 			nembed.add_field(name=embeds.EmptyEmbed, value=block)
# 			embedl.append(nembed)
# 		print(embedl)
# 		await ctx.followup.send(embeds=embedl[:10])
# 	except IndexError as ex:
# 		print(f"{type(ex).__name__} {ex}")
# 		await ctx.followup.send(content=f"Error: {ex}")


def setup(bot):
	bot.add_cog(Play(bot))
