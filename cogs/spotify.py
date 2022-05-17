import nextcord
from nextcord import SlashOption
import main
import datetime as dt
from utils.spotify_api_request import SpotifyApi
from cogs.play import search_yt, Play
from nextcord.ext import commands


class Spotify(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="spotify",
                            description="search on spotify",
                            guild_ids=main.bot.guild_ids)
    async def spotify(self, ctx, music: str = SlashOption(name="music",
                                                          description="choose music",
                                                          required=True)):
        await ctx.response.send_message('Bot is thinking!')
        embed = nextcord.Embed(title=f"Song added to queue from Spotify {self.bot.get_emoji(944554099175727124)}",
                               color=0x152875)
        embed.set_author(name="Worpal", icon_url="https://i.imgur.com/Rygy2KWs.jpg")
        artists = ""
        query = []
        if "open.spotify.com/track" in music:
            a = music.split('track/')
            a = a[1].split('?si')
            song = SpotifyApi().get_by_id(trackid=a[0])
            for artist in song['album']['artists']:
                artists += "".join("{}, ".format(artist['name']))
            artists = artists[:-2]
            embed.set_thumbnail(url=song['album']['images'][0]['url'])
            embed.add_field(name="{}\n\n".format(song['name']),
                            value="{}\n{}".format(artists, str(dt.timedelta(
                                seconds=int(int(song['duration_ms']) / 1000)))))
            query.append("{}\n{}".format(song['album']['name'], artists))
        elif "open.spotify.com/playlist" in music:
            a = music.split("playlist/")
            a = a[1].split("?si")
            playlist = SpotifyApi().get_playlist(playlist_id=a[0])
            for song in playlist['tracks']['items']:
                artists = ""
                for artist in song['track']['artists']:
                    artists += "".join("{}, ".format(artist['name']))
                artists = artists[:-2]
                query.append("{}\n{}".format(song['track']['name'], artists))
            embed.set_thumbnail(url=playlist['images'][0]['url'])
            embed.add_field(name="{}\n\n".format(playlist['name']),
                            value="{}\n".format(playlist['owner']['display_name']))
        else:
            song = SpotifyApi().get_by_name(q=music, limit=1, type_="track")
            for artist in song['tracks']['items'][0]['artists']:
                artists += "".join("{}, ".format(artist['name']))
            artists = artists[:-2]
            embed.set_thumbnail(url=song['tracks']['items'][0]['album']['images'][0]['url'])
            embed.add_field(name="{}\n\n".format(song['tracks']['items'][0]['name']),
                            value="{}\n{}".format(artists, str(dt.timedelta(
                                seconds=int(int(song['tracks']['items'][0]['duration_ms']) / 1000)))))
            query.append("{}  {}".format(song['tracks']['items'][0]['name'], artists))
        embed.set_footer(text="Song requested by: " + ctx.user.name)
        voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
        if ctx.user.voice:
            voice_channel = ctx.user.voice.channel
            for entry in query:
                track = search_yt(entry)
                if track is False:
                    await ctx.edit_original_message('Bot is thinking!')(content="Could not download the song. "
                                                                                "Incorrect format try another "
                                                                                "keyword. This could be due to "
                                                                                "playlist or a livestream format.")
                else:
                    main.bot.music_queue[ctx.guild.id].append([track, voice_channel])
            if main.bot.music_queue[ctx.guild.id][0]:
                await Play(commands.cog).play_music(ctx, voice)
            await ctx.edit_original_message(embed=embed)
        else:
            await ctx.edit_original_message(content="Connect to a voice channel!")


def setup(bot):
    bot.add_cog(Spotify(bot))
