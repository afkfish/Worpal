import datetime as dt
import random
import re

from discord import app_commands, Interaction, ui, ButtonStyle, VoiceClient, Embed, FFmpegOpusAudio, VoiceProtocol
from discord.ext import commands
from discord.utils import MISSING

from api.SpotifyAPI import SpotifyApi
from api.YouTubeAPI import get_link
from main import Worpal
from structures.playable import Playable, Playlist, Track

JSON_FORMAT = {'name': '', 'songs': []}
FFMPEG_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

track_pattern = re.compile(r"https://open\.spotify\.com/track/[A-Za-z0-9]+\?si=[A-Za-z0-9]+", re.IGNORECASE)
playlist_pattern = re.compile(r"https://open\.spotify\.com/playlist/[A-Za-z0-9]+\?si=[A-Za-z0-9]+", re.IGNORECASE)


async def process_query(bot: Worpal, interaction: Interaction, user_vc, playlist: Playlist):
    for track in playlist.tracks:
        track = await get_link(track)
        playlist.tracks.pop(0)
        if track:
            track.channel = user_vc
            bot.music_queue[interaction.guild_id].append(track)


def slist(bot: Worpal, interaction: Interaction) -> str:
    return "\n".join(track.title for track in bot.music_queue[interaction.guild_id])


def announce_song(bot: Worpal, interaction: Interaction, view=MISSING) -> None:
    track = bot.playing[interaction.guild_id]
    embed = Embed(title="Currently playing:", color=bot.color)
    embed.set_thumbnail(url=track.image)

    # Check if valid
    desc = f"{track.progress_bar()} `[{track.format_progress()}/{track.get_duration()}]`"
    embed.add_field(name=track.title, value=desc, inline=False)
    bot.loop.create_task(interaction.followup.send(embed=embed, view=view))


class Navigation(ui.View):
    def __init__(self, bot: Worpal):
        super().__init__(timeout=100)
        self.bot = bot
        self.embed = None

    @ui.button(emoji="🔄", style=ButtonStyle.red, disabled=True)
    async def replay(self, interaction: Interaction, button: ui.Button):
        self.stop()
        for child in self.children:
            child.disabled = False
        button.disabled = True
        button.style = ButtonStyle.green
        voice: VoiceClient | VoiceProtocol = interaction.guild.voice_client
        if voice:
            self.embed = Embed(title="Replaying 🔄", color=self.bot.color)
            self.bot.music_queue[interaction.guild_id].insert(0, self.bot.playing[interaction.guild_id])
            voice.stop()
            await Play(self.bot).play_audio(interaction)
            await interaction.response.edit_message(embed=self.embed, view=None)
            return

        await interaction.response.edit_message(view=self)

    @ui.button(emoji="▶️", style=ButtonStyle.grey)
    async def resume(self, interaction: Interaction, button: ui.Button):
        for child in self.children:
            child.disabled = False
        button.disabled = True
        button.style = ButtonStyle.green
        voice: VoiceClient | VoiceProtocol = interaction.guild.voice_client
        if voice and voice.is_paused():
            self.embed = Embed(title="Resumed ▶️", color=self.bot.color)
            voice.resume()
            await interaction.response.edit_message(embed=self.embed, view=None)
            return

        await interaction.response.edit_message(view=self)

    @ui.button(emoji="⏸️", style=ButtonStyle.grey)
    async def pause(self, interaction: Interaction, button: ui.Button):
        for child in self.children:
            child.disabled = False
        button.disabled = True
        button.style = ButtonStyle.green
        voice: VoiceClient | VoiceProtocol = interaction.guild.voice_client
        if voice and voice.is_playing():
            self.embed = Embed(title="Paused ⏸️", color=self.bot.color)
            voice.pause()
            await interaction.response.edit_message(embed=self.embed, view=None)
            return

        await interaction.response.edit_message(view=self)

    @ui.button(emoji="⏭️", style=ButtonStyle.grey)
    async def skip(self, interaction: Interaction, button: ui.Button):
        self.embed = Embed(title="Skipped ⏭️", color=self.bot.color)
        self.stop()
        for child in self.children:
            child.disabled = True
        button.style = ButtonStyle.green
        voice: VoiceClient | VoiceProtocol = interaction.guild.voice_client
        if voice:
            voice.stop()
            await Play(self.bot).play_audio(interaction)
            await interaction.response.edit_message(embed=self.embed, view=None)
            return

        await interaction.response.edit_message(view=self)


class Play(commands.Cog):

    def __init__(self, bot: Worpal):
        self.bot = bot

    @staticmethod
    async def ensure_voice(interaction: Interaction) -> bool:
        if not interaction.user.voice:
            await interaction.response.send_message(embed=Embed(title="Connect to a voice channel!"), ephemeral=True)
            return False
        return True

    def play_interrupt_handler(self, interaction: Interaction, error) -> None:
        if error:
            self.bot.logger.error(error)
            interaction.channel.send(embed=Embed(title="There was an error while trying to play the song."))

        self.bot.loop.create_task(self.play_audio(interaction))

    async def play_audio(self, interaction: Interaction) -> None:
        try:
            self.bot.music_queue[interaction.guild_id][0]
        except IndexError:
            return

        voice_client: VoiceClient | VoiceProtocol = interaction.guild.voice_client
        if not voice_client:
            voice_client = await self.bot.music_queue[interaction.guild_id][0].channel.connect()

        elif voice_client.is_playing():
            return

        elif voice_client.channel != (channel := self.bot.music_queue[interaction.guild_id][0].channel):
            await voice_client.move_to(channel)

        if self.bot.looping(interaction.guild_id):
            m_url = self.bot.playing[interaction.guild_id].source

        elif self.bot.shuffle(interaction.guild_id):
            entry: Track = random.choice(self.bot.music_queue[interaction.guild_id])
            m_url = entry.source
            self.bot.playing[interaction.guild_id] = entry
            self.bot.music_queue[interaction.guild_id].remove(entry)

        else:
            m_url = self.bot.music_queue[interaction.guild_id][0].source
            self.bot.playing[interaction.guild_id] = self.bot.music_queue[interaction.guild_id][0]
            self.bot.music_queue[interaction.guild_id].pop(0)

        if self.bot.announce(interaction.guild_id):
            announce_song(self.bot, interaction)

        voice_client.play(
            FFmpegOpusAudio(
                source=m_url,
                codec='copy',
                before_options=FFMPEG_OPTIONS
            ),
            after=lambda e: self.play_interrupt_handler(interaction, e),
            signal_type="music"
        )
        self.bot.playing[interaction.guild_id].start = dt.datetime.now()

    @app_commands.command(name="play", description="Play a song from youtube or spotify")
    @app_commands.check(ensure_voice)
    async def play(self, interaction: Interaction, query: str):
        await interaction.response.defer()

        playable = Playable(interaction.user, spotify=("spotify" in query))
        track: Track = Track.from_playable(playable, query)

        user_vc = interaction.user.voice.channel
        if track_pattern.match(query):
            track.id = re.search(r"track/(.+?)\?si", query).group(1)
            track = SpotifyApi().resolve(track)

        elif playlist_pattern.match(query):
            playlist = Playlist.from_playable(playable)
            playlist.id = re.search(r"playlist/(.+?)\?si", query).group(1)
            resolved: Playlist = SpotifyApi().resolve(playlist)

            await process_query(self.bot, interaction, user_vc, resolved)
            track: Track = resolved.get_first_track()

        track = await get_link(track)
        if not track:
            await interaction.followup.send(content="Couldn't play the song.", ephemeral=True)
            return

        track.channel = user_vc
        self.bot.music_queue[interaction.guild_id].append(track)

        if track.spotify:
            track.title += " " + str(self.bot.get_emoji(944554099175727124))

        await interaction.followup.send(embed=track.get_embed())
        await self.play_audio(interaction)

    @app_commands.command(name="playskip", description="Skip the current song and play the given one.")
    @app_commands.check(ensure_voice)
    async def playskip(self, interaction: Interaction, query: str):
        await interaction.response.defer()

        # first we check if the song can be played, so we are not interrupting
        # if something is already playing
        track = Track(query, interaction.user)
        track = await get_link(track)

        if not track:
            await interaction.followup.send(content="Couldn't play the song.", ephemeral=True)
            return

        # we check wether the bot is connected and stop playing,
        # if not, connect to user
        voice: VoiceClient | VoiceProtocol = interaction.guild.voice_client
        user_vc = interaction.user.voice.channel
        if not voice:
            await user_vc.connect()
        else:
            voice.stop()

        self.bot.music_queue[interaction.guild_id].insert(0, track)
        await interaction.followup.send(embed=track.get_embed())
        await self.play_audio(interaction)

    @app_commands.command(name='seek', description='Seek to a specific time in the song.')
    @app_commands.check(ensure_voice)
    async def seek(self, interaction: Interaction, time: int):
        await interaction.response.defer()

        voice_client: VoiceClient | VoiceProtocol = interaction.guild.voice_client
        user_vc = interaction.user.voice.channel

        if not self.bot.playing[interaction.guild_id]:
            await interaction.followup.send(content='You need to play a song before you can seek in it.')
            return

        m_url = self.bot.playing[interaction.guild_id].source

        if not voice_client:
            voice_client = await user_vc.connect()

        elif voice_client.channel != user_vc:
            await voice_client.move_to(user_vc)

        formatted_time = dt.timedelta(seconds=int(time))
        voice_client.stop()
        # play the song with discord.FFmpegOpusAudio
        voice_client.play(
            FFmpegOpusAudio(
                source=m_url,
                codec='copy',
                before_options=f'-ss {time} {FFMPEG_OPTIONS}'
            ),
            after=lambda e: self.play_interrupt_handler(interaction, e)
        )
        self.bot.playing[interaction.guild_id].start = dt.datetime.utcnow() - dt.timedelta(seconds=int(time))
        # send a message saying the bot is now playing the song
        await interaction.followup.send(
            embed=Embed(
                title=f'Now playing {self.bot.playing[interaction.guild_id].title} from {formatted_time} seconds.'
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
        if self.bot.playing[interaction.guild_id]:
            view = Navigation(self.bot)
            announce_song(self.bot, interaction, view)
            await view.wait()
            await interaction.edit_original_response(embed=view.embed, view=None)

        else:
            await interaction.followup.send(content="No song has been played yet!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Play(bot))
