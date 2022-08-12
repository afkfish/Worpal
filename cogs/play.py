import datetime as dt
import json
import random
import re

import nextcord
from nextcord import Embed, utils, SlashOption, slash_command, FFmpegPCMAudio, embeds, ui, ButtonStyle
from nextcord.ext import commands

import main
from utils.genius_api_request import GeniusApi
from utils.lyrics_scrape import get_lyrics
from utils.song_info import *
from utils.spotify_api_request import SpotifyApi

JSON_FORMAT = {'name': '', 'songs': []}


async def process_query(ctx, vc):
    for entry in main.bot.query[ctx.guild.id]:
        track = search_yt(entry)
        main.bot.query[ctx.guild.id].pop(0)
        if track:
            main.bot.music_queue[ctx.guild.id].append([track, vc])


def slist(ctx):
    li = ""
    for song in main.bot.music_queue[ctx.guild.id]:
        li += song[0]['title'] + "\n"
    return li


def announce_song(ctx, a, view=None):
    embed = Embed(title="Currently playing:", color=0x152875)
    embed.set_author(name="Worpal", icon_url=main.icon)
    embed.set_thumbnail(url=a[0]['thumbnail'])
    if len(main.bot.playing[ctx.guild.id]) > 2:
        timedelta = (dt.datetime.utcnow() - main.bot.playing[ctx.guild.id][-1]).total_seconds()
        rounded = int(timedelta)
        playtime = dt.timedelta(seconds=rounded)
        embed.add_field(name=a[0]['title'], value=f"Currently at:\n{playtime}", inline=True)
        embed.set_footer(text=str(dt.timedelta(seconds=int(a[0]['duration']))))
    else:
        embed.add_field(name=a[0]['title'], value=f"Lenght:\n{str(dt.timedelta(seconds=int(a[0]['duration'])))}",
                        inline=True)
    if view is not None:
        main.bot.loop.create_task(ctx.followup.send(embed=embed, view=view))
    else:
        main.bot.loop.create_task(ctx.followup.send(embed=embed))


class Navigation(ui.View):
    def __init__(self):
        super().__init__()

    @ui.button(label=":arrows_counterclockwise:", style=ButtonStyle.red, disabled=True)
    async def replay(self, button: ui.Button, ctx):
        self.stop()
        button.style = ButtonStyle.green
        await ctx.response.edit_message(view=self)

    @ui.button(label=":arrow_forward:", style=ButtonStyle.grey)
    async def resume(self, button: ui.Button, ctx):
        self.stop()
        button.style = ButtonStyle.green
        await ctx.response.edit_message(view=self)
        voice = utils.get(main.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            embed = Embed(title="Resumed :arrow_forward:")
            await ctx.send(embed=embed)

    @ui.button(label=":pause_button:", style=ButtonStyle.grey)
    async def pause(self, button: ui.Button, ctx):
        self.stop()
        button.style = ButtonStyle.green
        await ctx.response.edit_message(view=self)
        voice = utils.get(main.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            embed = Embed(title="Paused :pause_button:")
            await ctx.send(embed=embed)

    @ui.button(label="\:next_track:", style=ButtonStyle.grey)
    async def skip(self, button: ui.Button, ctx):
        self.stop()
        button.style = ButtonStyle.green
        await ctx.response.edit_message(view=self)
        voice = utils.get(main.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            voice.stop()
            await Play(commands.Cog).play_music(ctx, voice)
            embed = Embed(title="Skipped :next_track:")
            await ctx.send(embed=embed)


class Play(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def play_next(self, ctx):
        if len(main.bot.music_queue[ctx.guild.id]) > 0 or main.bot_loop(ctx.guild.id):
            vc = utils.get(main.bot.voice_clients, guild=ctx.guild)
            if vc is not None and not vc.is_playing():
                if main.bot_loop(ctx.guild.id):
                    m_url = main.bot.playing[ctx.guild.id][0]['source']
                elif main.bot_shuffle(ctx.guild.id):
                    a = random.choice(main.bot.music_queue[ctx.guild.id])
                    m_url = a[0]['source']
                    main.bot.playing[ctx.guild.id] = a
                    main.bot.music_queue[ctx.guild.id].remove(a)
                else:
                    m_url = main.bot.music_queue[ctx.guild.id][0][0]['source']
                    main.bot.playing[ctx.guild.id] = main.bot.music_queue[ctx.guild.id][0]
                    main.bot.music_queue[ctx.guild.id].pop(0)
                if main.bot_announce(ctx.guild.id):
                    announce_song(ctx, main.bot.playing[ctx.guild.id])
                vc.play(FFmpegPCMAudio(before_options='-reconnect 1 '
                                                      '-reconnect_streamed 1 '
                                                      '-reconnect_delay_max 5',
                                       source=m_url), after=self.play_next(ctx))
                main.bot.playing[ctx.guild.id].append(dt.datetime.utcnow())

    async def play_music(self, ctx, vc):
        if len(main.bot.music_queue[ctx.guild.id]) > 0:
            m_url = main.bot.music_queue[ctx.guild.id][0][0]['source']
            if vc is None:
                vc = await main.bot.music_queue[ctx.guild.id][0][1].connect()
            else:
                await vc.move_to(main.bot.music_queue[ctx.guild.id][0][1])
            if not vc.is_playing():
                main.bot.playing[ctx.guild.id] = main.bot.music_queue[ctx.guild.id][0]
                main.bot.music_queue[ctx.guild.id].pop(0)
                if main.bot_announce(ctx.guild.id):
                    announce_song(ctx, main.bot.music_queue[ctx.guild.id][0])
                if vc.is_connected():
                    vc.play(FFmpegPCMAudio(before_options='-reconnect 1 '
                                                          '-reconnect_streamed 1 '
                                                          '-reconnect_delay_max 5',
                                           source=m_url), after=self.play_next(ctx))
                    main.bot.playing[ctx.guild.id].append(dt.datetime.utcnow())

    @slash_command(name="play",
                   description="Play a song",
                   guild_ids=main.bot.guild_ids)
    async def play(self, ctx, music: str = SlashOption(name="music",
                                                       description="the music to be played",
                                                       required=True)):
        await ctx.response.defer()
        if ctx.user.voice:
            embed = Embed(title="Song added to queue" +
                                f" from Spotify {main.bot.get_emoji(944554099175727124)}" if "spotify" in music else "",
                          color=0x152875)
            embed.set_author(name="Worpal", icon_url=main.icon)
            if "open.spotify.com" in music:
                artists = ""
                if "/track" in music:
                    # https://open.spotify.com/track/5oKRyAx215xIycigG6NNwt?si=834b843759b84497
                    # https://open.spotify.com/track/2Oz3Tj8RbLBZFW5Adsyzyj?si=ae09611876c44d65
                    a = re.search("track/(.*)\?si", music).group(1)
                    song = SpotifyApi().get_by_id(trackid=a)
                    for artist in song['album']['artists']:
                        artists += "".join(f"{artist['name']}, ")
                    artists = artists[:-2]
                    embed.set_thumbnail(url=song['album']['images'][0]['url'])
                    embed.add_field(name=f"{song['name']}\n\n",
                                    value=f"{artists}\n"
                                          f"{str(dt.timedelta(seconds=round(song['duration_ms'] / 1000, 0)))}")
                    main.bot.query[ctx.guild.id].append(f"{song['name']}\t{artists}")
                elif "/playlist" in music:
                    a = re.search("playlist/(.*)\?si", music).group(1)
                    playlist = SpotifyApi().get_playlist(playlist_id=a)
                    count = 0
                    for song in playlist['tracks']['items']:
                        if count <= 10:
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
                                    value=f"{artists}\n"
                                          f"{str(dt.timedelta(seconds=round(song['duration_ms'] / 1000, 0)))}")
                    main.bot.query[ctx.guild.id].append(f"{song['name']}\t{artists}")
                embed.set_footer(text="Song requested by: " + ctx.user.name)
                voice = utils.get(main.bot.voice_clients, guild=ctx.guild)
                voice_channel = ctx.user.voice.channel
                await ctx.followup.send(embed=embed)
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
                voice = utils.get(main.bot.voice_clients, guild=ctx.guild)
                voice_channel = ctx.user.voice.channel
                song = search_yt(music)
                if not song:
                    await ctx.followup.send(content="Could not download the song. Incorrect format try another "
                                                    "keyword. This could be due to playlist or a livestream "
                                                    "format.")
                else:
                    main.bot.music_queue[ctx.guild.id].append([song, voice_channel])
                    embed.set_thumbnail(url=main.bot.music_queue[ctx.guild.id][-1][0]['thumbnail'])
                    embed.add_field(name=main.bot.music_queue[ctx.guild.id][-1][0]['title'],
                                    value=str(dt.timedelta(
                                        seconds=int(main.bot.music_queue[ctx.guild.id][-1][0]['duration']))),
                                    inline=True)
                    embed.set_footer(text="Song requested by: " + ctx.user.name)
                    await ctx.followup.send(embed=embed)
                    await self.play_music(ctx, voice)
        else:
            await ctx.followup.send(content="Connect to a voice channel!", ephemeral=True)

    @slash_command(name="queue",
                   description="Displays the songs in the queue",
                   guild_ids=main.bot.guild_ids)
    async def queue(self, ctx):
        await ctx.response.defer()
        embed = Embed(title="Queue", color=0x152875)
        embed.set_author(name="Worpal", icon_url=main.icon)
        songs = slist(ctx)
        if songs:
            embed.add_field(name="Songs: ", value=songs, inline=True)
        else:
            embed.add_field(name="Songs: ", value="No music in queue", inline=True)
        await ctx.followup.send(embed=embed)

    @slash_command(name="createpl",
                   description="Create playlists",
                   guild_ids=[940575531567546369])
    async def createplaylist(self, ctx, name: str = SlashOption(name="name",
                                                                description="playlist name",
                                                                required=True)):
        JSON_FORMAT['name'] = name
        with open("./playlists/{}.json".format(name), "w") as f:
            json.dump(JSON_FORMAT, f, indent=4)
        f.close()
        await ctx.response.send_message("Playlis {} was succefully created".format(name))

    @slash_command(name="addsong",
                   description="Append a song to existing playlists",
                   guild_ids=[940575531567546369])
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

    @slash_command(name="playlist",
                   description="Play songs from a playlist",
                   guild_ids=[940575531567546369])
    async def playlist(self, ctx, playlist_name: str = SlashOption(name="playlist_name",
                                                                   description="the name of the playlist",
                                                                   required=True)):
        with open("./playlists/{}.json".format(playlist_name), "r") as f:
            data = json.load(f)
        for item in data['songs']:
            vc = utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice_channel = ctx.user.voice.channel
            if voice_channel is None:
                await ctx.response.send_message("Connect to a voice channel!")
            else:
                song = search_yt(item)
                if song is False:
                    await ctx.response.send_message("Could not play the song from the playlist.")
                else:
                    main.bot.music_queue.append([song, voice_channel])
                    await self.play_music(ctx, vc)
        await ctx.response.send_message("Playlist succefully loaded!")

    @slash_command(name="np",
                   description="The song that is currently being played",
                   guild_ids=main.bot.guild_ids)
    async def np(self, ctx):
        await ctx.response.defer()
        if len(main.bot.playing[ctx.guild.id]) > 0:
            view = Navigation()
            announce_song(ctx, main.bot.playing[ctx.guild.id], view)
            await view.wait()

        else:
            await ctx.followup.send(content="No song has been played yet!", ephemeral=True)

    @slash_command(name="lyrics",
                   description="test",
                   guild_ids=[940575531567546369])  # still in beta and not working properly
    async def lyrics(self, ctx):
        await ctx.response.defer()
        embed = Embed(title="Song Lyrics:", color=0x152875)
        embed.set_author(name="Worpal", icon_url=main.icon)
        try:
            song = GeniusApi().get_song(main.bot.playing[ctx.guild.id][0]['title'])
            lyrics = get_lyrics(song)
            ly = []
            for i in range(round(len(lyrics) / 1024) - 1):
                ly.append(lyrics[i:i + 1024])
            embed.add_field(name=song["title"], value=embeds.EmptyEmbed)
            embed.set_thumbnail(url=main.bot.playing[ctx.guild.id][0]['thumbnail'])
            print(ly)
            print(len(ly))
            embedl = [embed]
            for block in ly:
                nembed = Embed(title=embeds.EmptyEmbed, color=0x152875)
                nembed.add_field(name=embeds.EmptyEmbed, value=block)
                embedl.append(nembed)
            print(embedl)
            await ctx.followup.send(embeds=embedl[:10])
        except IndexError as ex:
            print(f"{type(ex).__name__} {ex}")
            await ctx.followup.send(content=f"Error: {ex}")


def setup(bot):
    bot.add_cog(Play(bot))
