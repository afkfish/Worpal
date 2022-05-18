import nextcord
import datetime as dt
from nextcord.ext import commands
from cogs.play import Play
import main


# create a class for the cog
class Seek(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # create a seek command from cog_ext
    @nextcord.slash_command(name='seek',
                            description='Seek to a specific time in the song.',
                            guild_ids=main.bot.guild_ids)  # async function for command
    async def seek(self, ctx, time):
        # send a message saying that the bot is thinking with a 1-second lifespan
        await ctx.response.send_message('The bot is thinking...')
        # get the voice channel if there is one
        voice_channel = ctx.user.voice.channel
        voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
        # if the bot has playen a song before
        if len(main.bot.playing[ctx.guild.id]) != 0:
            m_url = main.bot.playing[ctx.guild.id][0]['source']
            # if there is no voice channel
            if voice_channel is None:
                # send a message saying you need to be in a voice channel
                await ctx.edit_original_message(content='You need to be in a voice channel to use this command.')
            else:
                # if there is a voice channel and the bot is not in it connect to it
                if voice == "" or voice is None:
                    voice = await main.bot.playing[ctx.guild.id][1].connect()

                else:
                    # move the bot to the voice
                    await voice.move_to(main.bot.playing[ctx.guild.id][1])
                formatted_time = dt.timedelta(seconds=int(time))
                voice.stop()
                # play the song with discord.FFmpegPCMaudio
                voice.play(nextcord.FFmpegPCMAudio(before_options=f'-ss {time} -reconnect 1 -reconnect_streamed 1 '
                                                                  '-reconnect_delay_max 5',
                                                   source=m_url),
                           after=lambda e: Play(commands.Cog).play_next(ctx, voice))
                # send a message saying the bot is now playing the song
                await ctx.edit_original_message(
                    content=f'Now playing {main.bot.playing[ctx.guild.id][0]["title"]} from {formatted_time} seconds.')
        else:
            # send a message to play a song in order to seek in it
            await ctx.edit_original_message(content='You need to play a song before you can seek in it.')


# add the cog to the bot
def setup(bot):
    bot.add_cog(Seek(bot))
