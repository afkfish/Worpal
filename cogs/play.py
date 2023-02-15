import datetime as dt
import random
import re

from discord import app_commands, Interaction, ui, ButtonStyle, VoiceClient, Embed, FFmpegPCMAudio
from discord.ext import commands

from api.SpotifyAPI import SpotifyApi
from api.YouTubeAPI import get_link
from main import Worpal
from structures.playlist import PlayList
from structures.track import Track

JSON_FORMAT = {'name': '', 'songs': []}
FFMPEG_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"


async def process_query(bot: Worpal, interaction: Interaction, user_vc, playlist: PlayList):
    for track in playlist.tracks:
        track = get_link(track)
        playlist.tracks.pop(0)
        if track.is_valid():
            track.channel = user_vc
            bot.music_queue[interaction.guild.id].append(track)


def slist(bot: Worpal, interaction: Interaction) -> str:
    li = ""
    for track in bot.music_queue[interaction.guild.id]:
        li += track.title + "\n"
    return li


def announce_song(bot: Worpal, interaction: Interaction, view=None) -> None:
    track = bot.playing[interaction.guild.id]
    embed = Embed(title="Currently playing:", color=bot.color)
    embed.set_thumbnail(url=track.thumbnail)
    playtime = dt.timedelta(seconds=(dt.datetime.utcnow() - bot.playing[interaction.guild.id].start).seconds)
    embed.add_field(name=track.title, value=f"Currently at:\n{playtime}", inline=True)
    embed.set_footer(text=str(dt.timedelta(seconds=int(track.duration))))

    if view is not None:
        bot.loop.create_task(interaction.followup.send(embed=embed, view=view))
    else:
        bot.loop.create_task(interaction.followup.send(embed=embed))


class Navigation(ui.View):
    def __init__(self, bot: Worpal):
        super().__init__(timeout=50)
        self.bot = bot

    @ui.button(emoji="🔄", style=ButtonStyle.red, disabled=True)
    async def replay(self, button: ui.Button, interaction: Interaction):
        self.stop()
        for child in self.children:
            child.disabled = True
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        voice: VoiceClient = interaction.guild.voice_client
        if voice is not None and isinstance(voice, VoiceClient):
            self.bot.music_queue[interaction.guild.id].insert(0, self.bot.playing[interaction.guild.id])
            voice.stop()
            await Play(self.bot).play_music(interaction)
            embed = Embed(title="Replaying 🔄")
            await interaction.followup.send(embed=embed)

    @ui.button(emoji="▶️", style=ButtonStyle.grey)
    async def resume(self, button: ui.Button, interaction: Interaction):
        self.stop()
        for child in self.children:
            child.disabled = True
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        voice: VoiceClient = interaction.guild.voice_client
        if isinstance(voice, VoiceClient) and voice.is_paused():
            voice.resume()
            embed = Embed(title="Resumed ▶️")
            await interaction.followup.send(embed=embed)

    @ui.button(emoji="⏸️", style=ButtonStyle.grey)
    async def pause(self, button: ui.Button, interaction: Interaction):
        self.stop()
        for child in self.children:
            child.disabled = True
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        voice: VoiceClient = interaction.guild.voice_client
        if isinstance(voice, VoiceClient) and voice.is_playing():
            voice.pause()
            embed = Embed(title="Paused ⏸️")
            await interaction.followup.send(embed=embed)

    @ui.button(emoji="⏭️", style=ButtonStyle.grey)
    async def skip(self, button: ui.Button, interaction: Interaction):
        self.stop()
        for child in self.children:
            child.disabled = True
        button.style = ButtonStyle.green
        await interaction.followup.send(view=self)
        voice: VoiceClient = interaction.guild.voice_client
        if voice is not None and isinstance(voice, VoiceClient):
            voice.stop()
            await Play(self.bot).play_music(interaction)
            embed = Embed(title="Skipped ⏭️")
            await interaction.followup.send(embed=embed)


class Play(commands.Cog):

    def __init__(self, bot: Worpal):
        self.bot = bot

    def play_next(self, interaction: Interaction):
        if len(self.bot.music_queue[interaction.guild.id]) == 0:
            return

        vc: VoiceClient = interaction.guild.voice_client
        if vc is None or not isinstance(vc, VoiceClient):
            return

        if vc.is_playing():
            return

        if self.bot.looping(str(interaction.guild.id)):
            m_url = self.bot.playing[interaction.guild.id].source

        elif self.bot.shuffle(str(interaction.guild.id)):
            entry: Track = random.choice(self.bot.music_queue[interaction.guild.id])
            m_url = entry.source
            self.bot.playing[interaction.guild.id] = entry
            self.bot.music_queue[interaction.guild.id].remove(entry)

        else:
            m_url = self.bot.music_queue[interaction.guild.id][0].source
            self.bot.playing[interaction.guild.id] = self.bot.music_queue[interaction.guild.id][0]
            self.bot.music_queue[interaction.guild.id].pop(0)

        if self.bot.announce(str(interaction.guild.id)):
            announce_song(self.bot, interaction)

        vc.play(
            FFmpegPCMAudio(
                source=m_url,
                before_options=FFMPEG_OPTIONS
            ),
            after=lambda e: self.bot.logger.error(e) and interaction.channel.send(
                Embed(title="There was an error playing the song.")) if e else self.play_next(interaction)
        )
        self.bot.playing[interaction.guild.id].start = dt.datetime.utcnow()

    async def play_music(self, interaction: Interaction):
        if len(self.bot.music_queue[interaction.guild.id]) == 0:
            return

        m_url = self.bot.music_queue[interaction.guild.id][0].source
        vc: VoiceClient = interaction.guild.voice_client

        if vc is None or not isinstance(vc, VoiceClient):
            vc = await self.bot.music_queue[interaction.guild.id][0].channel.connect()

        elif vc.channel != self.bot.music_queue[interaction.guild.id][0].channel:
            await vc.move_to(self.bot.music_queue[interaction.guild.id][0].channel)

        if vc.is_playing():
            return

        self.bot.playing[interaction.guild.id] = self.bot.music_queue[interaction.guild.id][0]
        self.bot.music_queue[interaction.guild.id].pop(0)

        if self.bot.announce(str(interaction.guild.id)):
            announce_song(self.bot, interaction)

        vc.play(
            FFmpegPCMAudio(
                source=m_url,
                before_options=FFMPEG_OPTIONS
            ),
            after=lambda e: self.bot.logger.error(e) and interaction.channel.send(
                Embed(title="There was an error playing the song.")) if e else self.play_next(interaction)
        )
        self.bot.playing[interaction.guild.id].start = dt.datetime.utcnow()

    @staticmethod
    async def ensure_voice(interaction: Interaction) -> bool:
        if not interaction.user.voice:
            await interaction.response.send_message(embed=Embed(title="Connect to a voice channel!"), ephemeral=True)
            return False
        return True

    @app_commands.command(name="play", description="Play a song")
    @app_commands.check(ensure_voice)
    async def play(self, interaction: Interaction, query: str):
        await interaction.response.defer()

        track = Track(query=query, user=interaction.user, spotify=True if "spotify" in query else False)

        user_vc = interaction.user.voice.channel
        if "open.spotify.com" not in query:
            track = get_link(track)
            if not track.is_valid():
                await interaction.followup.send(content="Couldn't play the song.", ephemeral=True)
                return

            track.channel = user_vc
            self.bot.music_queue[interaction.guild.id].append(track)
            await interaction.followup.send(embed=track.get_embed())
            await self.play_music(interaction)
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

            interaction.followup.send(embed=playlist.get_embed())
            track = playlist.tracks[0]

        track = get_link(track)
        if not track.is_valid():
            await interaction.followup.send(content="Couldn't play the song.", ephemeral=True)
            return

        track.channel = user_vc
        self.bot.music_queue[interaction.guild.id].append(track)
        await interaction.followup.send(embed=track.get_embed() if playlist is None else playlist.get_embed())
        await self.play_music(interaction)

        if playlist is not None:
            await process_query(self.bot, interaction, user_vc, playlist)

    @app_commands.command(name="playskip", description="Skip the current song and play the given one.")
    @app_commands.check(ensure_voice)
    async def playskip(self, interaction: Interaction, query: str):
        await interaction.response.defer()

        voice: VoiceClient = interaction.guild.voice_client
        voice_channel = interaction.user.voice.channel
        if voice is None and not isinstance(voice, VoiceClient):
            await interaction.followup.send(content="Bot is not connected! Try playing a song first.", ephemeral=True)
            return

        voice.stop()
        track = Track(query=query, user=interaction.user)
        track = get_link(track)

        if not track.is_valid():
            await interaction.followup.send(content="Couldn't play the song.", ephemeral=True)
            return

        self.bot.music_queue[interaction.guild.id].insert(0, [track, voice_channel])
        await interaction.followup.send(embed=track.get_embed())
        await self.play_music(interaction)

    @app_commands.command(name='seek', description='Seek to a specific time in the song.')
    @app_commands.check(ensure_voice)
    async def seek(self, interaction: Interaction, time: int):
        await interaction.response.defer()

        voice: VoiceClient = interaction.guild.voice_client
        user_vc = interaction.user.voice.channel

        if len(self.bot.playing[interaction.guild.id]) == 0:
            await interaction.followup.send(content='You need to play a song before you can seek in it.')
            return

        m_url = self.bot.playing[interaction.guild.id].source

        if voice is None:
            voice = await user_vc.connect()

        elif voice.channel != user_vc:
            await voice.move_to(user_vc)

        formatted_time = dt.timedelta(seconds=int(time))
        voice.stop()
        # play the song with discord.FFmpegPCMaudio
        voice.play(
            FFmpegPCMAudio(
                before_options=f'-ss {time} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                source=m_url
            ),
            after=lambda e: self.bot.logger.error(e) if e else Play(self.bot).play_next(interaction)
        )
        self.bot.playing[interaction.guild.id][0].start = dt.datetime.utcnow() - dt.timedelta(seconds=int(time))
        # send a message saying the bot is now playing the song
        await interaction.followup.send(
            content=f'Now playing {self.bot.playing[interaction.guild.id].title} from {formatted_time} seconds.')

    @app_commands.command(name="queue", description="Displays the songs in the queue")
    async def queue(self, interaction: Interaction):
        await interaction.response.defer()
        embed = Embed(title="Queue", color=self.bot.color)
        songs = slist(self.bot, interaction)
        if songs:
            embed.add_field(name="Songs: ", value=songs, inline=True)
        else:
            embed.add_field(name="Songs: ", value="No music in queue", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="np", description="The song that is currently being played")
    async def np(self, interaction: Interaction):
        await interaction.response.defer()
        if len(self.bot.playing[interaction.guild.id]) > 0:
            view = Navigation(self.bot)
            announce_song(self.bot, interaction, view)
            await view.wait()

        else:
            await interaction.followup.send(content="No song has been played yet!", ephemeral=True)

# still in beta and not working properly
# @app_commands.command(name="lyrics",
# 			   description="test",
# 			   guild_ids=[940575531567546369])
# async def lyrics(self, interaction):
# 	await interaction.response.defer()
# 	embed = Embed(title="Song Lyrics:", color=bot.color)
#
# 	try:
# 		song = GeniusApi().get_song(bot.playing[interaction.guild.id][0]['title'])
# 		lyrics = get_lyrics(song)
# 		ly = []
# 		for i in range(round(len(lyrics) / 1024) - 1):
# 			ly.append(lyrics[i:i + 1024])
# 		embed.add_field(name=song["title"], value=embeds.EmptyEmbed)
# 		embed.set_thumbnail(url=bot.playing[interaction.guild.id][0]['thumbnail'])
# 		print(ly)
# 		print(len(ly))
# 		embedl = [embed]
# 		for block in ly:
# 			nembed = Embed(title=embeds.EmptyEmbed, color=bot.color)
# 			nembed.add_field(name=embeds.EmptyEmbed, value=block)
# 			embedl.append(nembed)
# 		print(embedl)
# 		await interaction.followup.send(embeds=embedl[:10])
# 	except IndexError as ex:
# 		print(f"{type(ex).__name__} {ex}")
# 		await interaction.followup.send(content=f"Error: {ex}")


async def setup(bot):
    await bot.add_cog(Play(bot))
