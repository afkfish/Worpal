import nextcord
from nextcord import SlashOption
import random
import json
import datetime as dt
# import youtube_transcript_api
from utils.genius_api_request import GeniusApi
from utils.lyrics_scrape import get_lyrics
from youtube_dl import YoutubeDL
from nextcord.ext import commands
import main

# from youtube_transcript_api import YouTubeTranscriptApi

YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn'}
JSON_FORMAT = {'name': '', 'songs': []}


# searching the item on YouTube
def search_yt(item):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            if item.startswith("https://www.youtube.com/watch?v="):
                info = ydl.extract_info(item, download=False)
            else:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
        except ValueError:
            return False

    return {'source': info['formats'][0]['url'], 'title': info['title'], 'thumbnail': info['thumbnail'],
            'duration': info['duration'], 'id': info['id']}


class Play(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def slist(ctx):
        slist = ""
        for song in main.bot.music_queue[ctx.guild.id]:
            slist += song[0]['title'] + "\n"
        return slist

    @staticmethod
    def announce_song(ctx, a):
        embed = nextcord.Embed(title="Currently playing:", color=0x152875)
        embed.set_author(name="Worpal", icon_url="https://i.imgur.com/Rygy2KWs.jpg")
        embed.set_thumbnail(url=a[0]['thumbnail'])
        embed.add_field(name=a[0]['title'],
                        value=str(dt.timedelta(seconds=int(a[0]['duration']))),
                        inline=True)
        main.bot.loop.create_task(ctx.edit_original_message(embed=embed))

    def play_next(self, ctx):
        if len(main.bot.music_queue[ctx.guild.id]) > 0 or main.bot_loop(ctx.guild.id):
            # get the first url and
            # remove the selected element as you are currently playing it
            vc = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
            if vc is not None and not vc.is_playing():
                if main.bot_shuffle(ctx.guild.id):
                    if main.bot_loop(ctx.guild.id):
                        m_url = main.bot.playing[ctx.guild.id][0]['source']
                    else:
                        a = random.choice(main.bot.music_queue[ctx.guild.id])
                        m_url = a[0]['source']
                        main.bot.playing[ctx.guild.id] = a
                        main.bot.music_queue[ctx.guild.id].remove(a)
                else:
                    if main.bot_loop(ctx.guild.id):
                        m_url = main.bot.playing[ctx.guild.id][0]['source']
                    else:
                        m_url = main.bot.music_queue[ctx.guild.id][0][0]['source']
                        main.bot.playing[ctx.guild.id] = main.bot.music_queue[ctx.guild.id][0]
                        main.bot.music_queue[ctx.guild.id].pop(0)
                if main.bot_announce(ctx.guild.id):
                    self.announce_song(ctx, main.bot.playing[ctx.guild.id])
                vc.play(nextcord.FFmpegPCMAudio(before_options='-reconnect 1 '
                                                               '-reconnect_streamed 1 '
                                                               '-reconnect_delay_max 5',
                                                source=m_url), after=lambda e: self.play_next(ctx))

    # infinite loop checking
    async def play_music(self, ctx, vc):
        m_url = main.bot.music_queue[ctx.guild.id][0][0]['source']
        # try to connect to voice channel if you are not already connected
        if vc is None:
            vc = await main.bot.music_queue[ctx.guild.id][0][1].connect()
        else:
            await vc.move_to(main.bot.music_queue[ctx.guild.id][0][1])
        # remove the first element as you are currently playing it
        if not vc.is_playing():
            if main.bot_announce(ctx.guild.id):
                self.announce_song(ctx, main.bot.music_queue[ctx.guild.id][0])
            main.bot.playing[ctx.guild.id] = main.bot.music_queue[ctx.guild.id][0]
            main.bot.music_queue[ctx.guild.id].pop(0)
            if vc.is_connected():
                vc.play(nextcord.FFmpegPCMAudio(before_options='-reconnect 1 '
                                                               '-reconnect_streamed 1 '
                                                               '-reconnect_delay_max 5',
                                                source=m_url), after=lambda e: self.play_next(ctx))

    @nextcord.slash_command(name="play",
                            description="Play a song",
                            guild_ids=main.bot.guild_ids)
    async def play(self, ctx, music: str = SlashOption(name="music",
                                                       description="the music to be played",
                                                       required=True)):
        await ctx.response.send_message('Bot is thinking!')
        query = "".join(music)
        voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
        if ctx.user.voice:
            voice_channel = ctx.user.voice.channel
            song = search_yt(query)
            if not song:
                await ctx.edit_original_message(content="Could not download the song. Incorrect format try another "
                                                        "keyword. This could be due to playlist or a livestream "
                                                        "format.")
            else:
                main.bot.music_queue[ctx.guild.id].append([song, voice_channel])
                embed = nextcord.Embed(title="Song added to queue", color=0x152875)
                embed.set_author(name="Worpal", icon_url="https://i.imgur.com/Rygy2KWs.jpg")
                embed.set_thumbnail(url=main.bot.music_queue[ctx.guild.id][-1][0]['thumbnail'])
                embed.add_field(name=main.bot.music_queue[ctx.guild.id][-1][0]['title'],
                                value=str(dt.timedelta(
                                    seconds=int(main.bot.music_queue[ctx.guild.id][-1][0]['duration']))),
                                inline=True)
                embed.set_footer(text="Song requested by: " + ctx.user.name)
                await ctx.edit_original_message(embed=embed)
                await self.play_music(ctx, voice)
        else:
            await ctx.edit_original_message(content="Connect to a voice channel!")

    @nextcord.slash_command(name="queue",
                            description="Displays the songs in the queue",
                            guild_ids=main.bot.guild_ids)
    async def queue(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        embed = nextcord.Embed(title="Queue", color=0x152875)
        embed.set_author(name="Worpal", icon_url="https://i.imgur.com/Rygy2KWs.jpg")
        songs = self.slist(ctx)
        if songs != "":
            embed.add_field(name="Songs: ", value=songs, inline=True)
        else:
            embed.add_field(name="Songs: ", value="No music in queue", inline=True)
        await ctx.edit_original_message(embed=embed)

    @nextcord.slash_command(name="createpl",
                            description="Create playlists",
                            guild_ids=main.bot.guild_ids)
    async def createplaylist(self, ctx, name: str = SlashOption(name="name",
                                                                description="playlist name",
                                                                required=True)):
        JSON_FORMAT['name'] = name
        with open("./playlists/{}.json".format(name), "w") as f:
            json.dump(JSON_FORMAT, f, indent=4)
        f.close()
        await ctx.response.send_message("Playlis {} was succefully created".format(name))

    @nextcord.slash_command(name="addsong",
                            description="Append a song to existing playlists",
                            guild_ids=main.bot.guild_ids)
    async def addsong(self, ctx,
                      playlist: str = SlashOption(name="playlist",
                                                  description="the destination playlist",
                                                  required=True),
                      song: str = SlashOption(name="song",
                                              description="the song's URL",
                                              required=True)):
        with open("./playlists/{}.json".format(playlist), "r") as a:
            data = json.load(a)
        data['songs'].append(song)
        with open("./playlists/{}.json".format(playlist), "w") as f:
            json.dump(data, f, indent=4)
        await ctx.response.send_message("Song was successfully added!")

    @nextcord.slash_command(name="playlist",
                            description="Play songs from a playlist",
                            guild_ids=main.bot.guild_ids)
    async def playlist(self, ctx, playlist_name: str = SlashOption(name="playlist_name",
                                                                   description="the name of the playlist",
                                                                   required=True)):
        with open("./playlists/{}.json".format(playlist_name), "r") as f:
            data = json.load(f)
        for item in data['songs']:
            vc = nextcord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice_channel = ctx.user.voice.channel
            if voice_channel is None:
                await ctx.response.send_message("Connect to a voice channel!")
            else:
                song = search_yt(item)
                # print(item)
                if song is False:
                    await ctx.response.send_message("Could not play the song from the playlist.")
                else:
                    main.bot.music_queue.append([song, voice_channel])
                    await self.play_music(ctx, vc)
        await ctx.response.send_message("Playlist succefully loaded!")

    @nextcord.slash_command(name="np",
                            description="The song that is currently being played",
                            guild_ids=main.bot.guild_ids)
    async def np(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        self.announce_song(ctx, main.bot.playing[ctx.guild.id])

    # @nextcord.slash_command(name="subtitle",
    #                   description="get the video subtitle",
    #                   guild_ids=main.bot.guild_ids)
    # async def subtitle(self, ctx):
    #     try:
    #         sub = YouTubeTranscriptApi.get_transcripts(video_ids=[main.bot.playing[ctx.guild.id][0]['id']],
    #                                                    languages=['en'])
    #         formatted = "```"
    #         for text in sub[0][main.bot.playing[ctx.guild.id][0]['id']]:
    #             formatted += text['text'] + "\n"
    #         formatted += "```"
    #         await ctx.response.send_message("Subtitle:")
    #         await ctx.response.send_message(formatted)
    #     except youtube_transcript_api._errors.TranscriptsDisabled as e:
    #         print("{}".format(type(e).__name__, e))
    #         await ctx.response.send_message("Couldn't find subtitles!")

    @nextcord.slash_command(name="lyrics",
                            description="test",
                            guild_ids=main.bot.guild_ids)
    async def lyrics(self, ctx):
        await ctx.response.send_message('Bot is thinking!', delete_after=1)
        embed = nextcord.Embed(title="Song Lyrics:", color=0x152875)
        embed.set_author(name="Worpal", icon_url="https://i.imgur.com/Rygy2KWs.jpg")
        try:
            song = GeniusApi().get_song(main.bot.playing[ctx.guild.id][0]['title'])
            lyrics = get_lyrics(song)
            if len(lyrics) > 1000:
                ly1 = lyrics[:len(lyrics) // 2]
                ly2 = lyrics[len(lyrics) // 2:]
                embed.add_field(name=song['title'], value=ly1)
                embed2 = nextcord.Embed(color=0x152875)
                embed2.add_field(name="", value=ly2)
                embed.set_thumbnail(url=main.bot.playing[ctx.guild.id][0]['thumbnail'])
                await ctx.response.send_message(embed=embed)
                await ctx.response.send_message(embed=embed2)
            else:
                embed.add_field(name=song['title'], value=lyrics)
                embed.set_thumbnail(url=main.bot.playing[ctx.guild.id][0]['thumbnail'])
                await ctx.response.send_message(embed=embed)
        except IndexError as ex:
            print(f"{type(ex).__name__} {ex}")
            await ctx.response.send_message(f"Error: {ex}")


def setup(bot):
    bot.add_cog(Play(bot))
