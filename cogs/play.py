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

track_pattern = re.compile(r"https://open\.spotify\.com/track/[A-Za-z0-9]+\?si=[A-Za-z0-9]+", re.IGNORECASE)
playlist_pattern = re.compile(r"https://open\.spotify\.com/playlist/[A-Za-z0-9]+\?si=[A-Za-z0-9]+", re.IGNORECASE)


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

    if view:
        desc = f"{track.progress_bar()} `[{track.format_progress()}/{track.get_duration()}]`"
        embed.add_field(name=track.title, value=desc, inline=False)
        bot.loop.create_task(interaction.followup.send(embed=embed, view=view))
    else:
        bot.loop.create_task(interaction.followup.send(embed=embed))


class Navigation(ui.View):
    def __init__(self, bot: Worpal):
        super().__init__(timeout=100)
        self.bot = bot

    @ui.button(emoji="🔄", style=ButtonStyle.red, disabled=True)
    async def replay(self, interaction: Interaction, button: ui.Button):
        self.stop()
        for child in self.children:
            child.disabled = False
        button.disabled = True
        button.style = ButtonStyle.green
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            self.bot.music_queue[interaction.guild.id].insert(0, self.bot.playing[interaction.guild.id])
            voice.stop()
            await Play(self.bot).play_music(interaction)
            embed = Embed(title="Replaying 🔄", color=self.bot.color)
            await interaction.response.edit_message(embed=embed, view=None)
            return

        await interaction.response.edit_message(view=self)

    @ui.button(emoji="▶️", style=ButtonStyle.grey)
    async def resume(self, interaction: Interaction, button: ui.Button):
        self.stop()
        for child in self.children:
            child.disabled = False
        button.disabled = True
        button.style = ButtonStyle.green
        await interaction.response.edit_message(view=self)
        voice: VoiceClient = interaction.guild.voice_client
        if voice and voice.is_paused():
            voice.resume()
            embed = Embed(title="Resumed ▶️", color=self.bot.color)
            await interaction.response.edit_message(embed=embed, view=None)
            return

        await interaction.response.edit_message(view=self)

    @ui.button(emoji="⏸️", style=ButtonStyle.grey)
    async def pause(self, interaction: Interaction, button: ui.Button):
        self.stop()
        for child in self.children:
            child.disabled = False
        button.disabled = True
        button.style = ButtonStyle.green
        voice: VoiceClient = interaction.guild.voice_client
        if voice and voice.is_playing():
            voice.pause()
            embed = Embed(title="Paused ⏸️", color=self.bot.color)
            await interaction.response.edit_message(embed=embed, view=None)
            return

        await interaction.response.edit_message(view=self)

    @ui.button(emoji="⏭️", style=ButtonStyle.grey)
    async def skip(self, interaction: Interaction, button: ui.Button):
        self.stop()
        for child in self.children:
            child.disabled = True
        button.style = ButtonStyle.green
        voice: VoiceClient = interaction.guild.voice_client
        if voice:
            voice.stop()
            await Play(self.bot).play_music(interaction)
            embed = Embed(title="Skipped ⏭️", color=self.bot.color)
            await interaction.response.edit_message(embed=embed, view=None)
            return

        await interaction.response.edit_message(view=self)


class Play(commands.Cog):

    def __init__(self, bot: Worpal):
        self.bot = bot

    def play_interrupt_handler(self, interaction: Interaction, error):
        if error:
            self.bot.logger.error(error)
            interaction.channel.send(Embed(title="There was an error while trying to play the song."))

        self.play_next(interaction)

    def play_next(self, interaction: Interaction):
        # if self.bot.music_queue[interaction.guild.id]:
        #     return

        # failsafe when the above code doesn't detect empty list
        try:
            temp = self.bot.music_queue[interaction.guild.id][0]
        except IndexError:
            return

        vc: VoiceClient = interaction.guild.voice_client
        if not vc:
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
            after=lambda e: self.play_interrupt_handler(interaction, e)
        )
        self.bot.playing[interaction.guild.id].start = dt.datetime.utcnow()

    async def play_music(self, interaction: Interaction):
        if not self.bot.music_queue[interaction.guild.id]:
            return

        m_url = self.bot.music_queue[interaction.guild.id][0].source
        vc: VoiceClient = interaction.guild.voice_client

        if not vc:
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
            after=lambda e: self.play_interrupt_handler(interaction, e)
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

        track = Track(query=query, user=interaction.user, spotify=bool("spotify" in query))

        user_vc = interaction.user.voice.channel
        playlist = None
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

        elif track_pattern.match(query):
            # https://open.spotify.com/track/5oKRyAx215xIycigG6NNwt?si=834b843759b84497
            # https://open.spotify.com/track/2Oz3Tj8RbLBZFW5Adsyzyj?si=ae09611876c44d65
            try:
                track_id = re.search(r"track/(.+?)\?si", query).group(1)
                track.id = track_id
                track = SpotifyApi().get_by_id(track=track)
            except AttributeError:
                interaction.followup.send(embed=Embed(title="Error in getting song from spotify!"))
                return

        elif playlist_pattern.match(query):
            try:
                playlist_id = re.search(r"playlist/(.+?)\?si", query).group(1)
                playlist = SpotifyApi().get_playlist(playlist_id=playlist_id)
            except AttributeError:
                interaction.followup.send(embed=Embed(title="Error in getting playlist from spotify!"))
                return

            interaction.followup.send(embed=playlist.get_embed())
            track = playlist.tracks[0]

        track = get_link(track)
        if not track.is_valid():
            await interaction.followup.send(content="Couldn't play the song.", ephemeral=True)
            return

        if track.spotify:
            track.title += " " + str(self.bot.get_emoji(944554099175727124))
        track.channel = user_vc
        self.bot.music_queue[interaction.guild.id].append(track)
        await interaction.followup.send(embed=playlist.get_embed() if playlist else track.get_embed())
        await self.play_music(interaction)

        if playlist:
            await process_query(self.bot, interaction, user_vc, playlist)

    @app_commands.command(name="playskip", description="Skip the current song and play the given one.")
    @app_commands.check(ensure_voice)
    async def playskip(self, interaction: Interaction, query: str):
        await interaction.response.defer()

        # first we check if the song can be played, so we are not interrupting
        # if something is already playing
        track = Track(query=query, user=interaction.user)
        track = get_link(track)

        if not track.is_valid():
            await interaction.followup.send(content="Couldn't play the song.", ephemeral=True)
            return

        # we check wether the bot is connected and stop playing,
        # if not, connect to user
        voice: VoiceClient = interaction.guild.voice_client
        user_vc = interaction.user.voice.channel
        if not voice:
            await user_vc.connect()
        else:
            voice.stop()

        self.bot.music_queue[interaction.guild.id].insert(0, track)
        await interaction.followup.send(embed=track.get_embed())
        await self.play_music(interaction)

    @app_commands.command(name='seek', description='Seek to a specific time in the song.')
    @app_commands.check(ensure_voice)
    async def seek(self, interaction: Interaction, time: int):
        await interaction.response.defer()

        voice: VoiceClient = interaction.guild.voice_client
        user_vc = interaction.user.voice.channel

        if self.bot.playing[interaction.guild.id]:
            await interaction.followup.send(content='You need to play a song before you can seek in it.')
            return

        m_url = self.bot.playing[interaction.guild.id].source

        if not voice:
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
            after=lambda e: self.play_interrupt_handler(interaction, e)
        )
        self.bot.playing[interaction.guild.id].start = dt.datetime.utcnow() - dt.timedelta(seconds=int(time))
        # send a message saying the bot is now playing the song
        await interaction.followup.send(
            embed=Embed(
                title=f'Now playing {self.bot.playing[interaction.guild.id].title} from {formatted_time} seconds.'
            )
        )

    @app_commands.command(name="queue", description="Displays the songs in the queue")
    async def queue(self, interaction: Interaction):
        await interaction.response.defer()
        embed = Embed(title="Queue", color=Worpal.color)
        songs = slist(self.bot, interaction)
        if songs:
            embed.add_field(name="Songs: ", value=songs)
        else:
            embed.add_field(name="Songs: ", value="No music in queue")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="np", description="The song that is currently being played")
    async def np(self, interaction: Interaction):
        await interaction.response.defer()
        if self.bot.playing[interaction.guild.id]:
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
