import datetime

import nextcord
from nextcord import SlashOption
import random
import json
import re
import datetime as dt
# import youtube_transcript_api
from utils.spotify_api_request import SpotifyApi
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


async def process_query(ctx, vc):
    for entry in main.bot.query[ctx.guild.id]:
        track = search_yt(entry)
        main.bot.query[ctx.guild.id].pop(0)
        if track:
            main.bot.music_queue[ctx.guild.id].append([track, vc])


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
        if len(main.bot.playing[ctx.guild.id]) > 2:
            timedelta = (datetime.datetime.utcnow() - main.bot.playing[ctx.guild.id][-1]).total_seconds()
            rounded = int(timedelta)
            playtime = datetime.timedelta(seconds=rounded)
            embed.add_field(name=a[0]['title'], value=f"Currently at:\n{playtime}", inline=True)
            embed.set_footer(text=str(dt.timedelta(seconds=int(a[0]['duration']))))
        else:
            embed.add_field(name=a[0]['title'], value=f"Lenght:\n{str(dt.timedelta(seconds=int(a[0]['duration'])))}",
                            inline=True)
        main.bot.loop.create_task(ctx.send(embed=embed))

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
                main.bot.playing[ctx.guild.id].append(datetime.datetime.utcnow())

    # infinite loop checking
    async def play_music(self, ctx, vc):
        if len(main.bot.music_queue[ctx.guild.id]) > 0:
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
                    main.bot.playing[ctx.guild.id].append(datetime.datetime.utcnow())

    @nextcord.slash_command(name="play",
                            description="Play a song",
                            guild_ids=main.bot.guild_ids)
    async def play(self, ctx, music: str = SlashOption(name="music",
                                                       description="the music to be played",
                                                       required=True)):
        await ctx.response.send_message('Bot is thinking!')
        embed = nextcord.Embed(title="Song added to queue" + f"from Spotify {main.bot.get_emoji(944554099175727124)}"
                                                             if "spotify" in music else "", color=0x152875)
        embed.set_author(name="Worpal", icon_url="https://i.imgur.com/Rygy2KWs.jpg")
        if "open.spotify.com" in music:
            artists = ""
            if "/track" in music:
                # https://open.spotify.com/track/5oKRyAx215xIycigG6NNwt?si=834b843759b84497
                a = re.search("track/(.*)\?si", music).group(1)
                song = SpotifyApi().get_by_id(trackid=a)
                for artist in song['album']['artists']:
                    artists += "".join("{}, ".format(artist['name']))
                artists = artists[:-2]
                embed.set_thumbnail(url=song['album']['images'][0]['url'])
                embed.add_field(name=f"{song['name']}\n\n",
                                value=f"{artists}\n{str(dt.timedelta(seconds=round(song['duration_ms'] / 1000, 0)))}")
                main.bot.query[ctx.guild.id].append(f"{song['name']}\t{artists}")
            elif "/playlist" in music:
                a = re.search("playlist/(.*)\?si", music).group(1)
                playlist = SpotifyApi().get_playlist(playlist_id=a)
                count = 0
                for song in playlist['tracks']['items']:
                    if count != 10:
                        artists = ""
                        count += 1
                        for artist in song['track']['artists']:
                            artists += "".join(f"{artist['name']}, ")
                        artists = artists[:-2]
                        main.bot.query[ctx.guild.id].append(f"{song['track']['name']}\t{artists}")
                embed.title = f"Playlist added to queue from Spotify {self.bot.get_emoji(944554099175727124)}"
                embed.set_thumbnail(url=playlist['images'][0]['url'])
                embed.add_field(name=f"{playlist['name']}\n\n",
                                value=f"{playlist['owner']['display_name']}\n")
            else:
                song = SpotifyApi().get_by_name(q=music, limit=1, type_="track")['tracks']['items'][0]
                for artist in song['artists']:
                    artists += "".join(f"{artist['name']}, ")
                artists = artists[:-2]
                embed.set_thumbnail(url=song['album']['images'][0]['url'])
                embed.add_field(name=f"{song['name']}\n\n",
                                value=f"{artists}\n{str(dt.timedelta(seconds=round(song['duration_ms'] / 1000, 0)))}")
                main.bot.query[ctx.guild.id].append(f"{song['name']}\t{artists}")
            embed.set_footer(text="Song requested by: " + ctx.user.name)
            voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
            if ctx.user.voice:
                voice_channel = ctx.user.voice.channel
                await ctx.edit_original_message(embed=embed)
                track = search_yt(main.bot.query[ctx.guild.id][0])
                main.bot.query[ctx.guild.id].pop(0)
                if track is False:
                    if len(main.bot.query[ctx.guild.id]) > 0:
                        await process_query(ctx, voice_channel)
                        await self.play_music(ctx, voice)
                else:
                    main.bot.music_queue[ctx.guild.id].append([track, voice_channel])
                    await self.play_music(ctx, voice)
                    if len(main.bot.query[ctx.guild.id]) > 0:
                        await process_query(ctx, voice_channel)
            else:
                await ctx.edit_original_message(content="Connect to a voice channel!")
        else:
            voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
            if ctx.user.voice:
                voice_channel = ctx.user.voice.channel
                song = search_yt(music)
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
        await ctx.response.send_message('Bot is thinking!')
        embed = nextcord.Embed(title="Song Lyrics:", color=0x152875)
        embed.set_author(name="Worpal", icon_url="https://i.imgur.com/Rygy2KWs.jpg")
        try:
            song = GeniusApi().get_song(main.bot.playing[ctx.guild.id][0]['title'])
            lyrics = get_lyrics(song)
            ly = []
            for i in range(round(len(lyrics)/1024)-1):
                ly.append(lyrics[i:i+1024])
            embed.add_field(name=song["title"], value=nextcord.embeds.EmptyEmbed)
            embed.set_thumbnail(url=main.bot.playing[ctx.guild.id][0]['thumbnail'])
            print(ly)
            print(len(ly))
            embeds = [embed]
            for block in ly:
                nembed = nextcord.Embed(title=nextcord.embeds.EmptyEmbed, color=0x152875)
                nembed.add_field(name=nextcord.embeds.EmptyEmbed, value=block)
                embeds.append(nembed)
            print(embeds)
            await ctx.edit_original_message(embeds=embeds[:10])
        except IndexError as ex:
            print(f"{type(ex).__name__} {ex}")
            await ctx.edit_original_message(content=f"Error: {ex}")


def setup(bot):
    bot.add_cog(Play(bot))
