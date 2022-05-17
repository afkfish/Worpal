import nextcord
from nextcord.ext import commands

import main
from cogs.play import Play


class Navigation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="skip",
                            description="Skip the current song",
                            guild_ids=main.bot.guild_ids)
    async def skip(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            voice.stop()
            embed = nextcord.Embed(title="Skipped :next_track:")
            await ctx.edit_original_message(embed=embed)
            # try to play next in the queue if it exists
            if voice.is_playing():
                obj = Play(commands.Cog)
                await obj.play_music(ctx, voice)

    @nextcord.slash_command(name="pause",
                            description="Pause the song",
                            guild_ids=main.bot.guild_ids)
    async def pause_(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            embed = nextcord.Embed(title="Paused :pause_button:")
            await ctx.edit_original_message(embed=embed)
            voice.pause()

    @nextcord.slash_command(name="resume",
                            description="Resume playing",
                            guild_ids=main.bot.guild_ids)
    async def resume_(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            embed = nextcord.Embed(title="Resumed")
            await ctx.edit_original_message(embed=embed)
            voice.resume()

    @nextcord.slash_command(name="stop",
                            description="Stop playing",
                            guild_ids=main.bot.guild_ids)
    async def stop_(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
        embed = nextcord.Embed(title="Stopped :stop_button:")
        await ctx.edit_original_message(embed=embed)
        voice.stop()

    @nextcord.slash_command(name="leave",
                            description="Leave voice chat",
                            guild_ids=main.bot.guild_ids)
    async def leave_(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        voice = nextcord.utils.get(main.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            await voice.disconnect()
            await ctx.edit_original_message(content="Disconnected!")

    @nextcord.slash_command(name="clear",
                            guild_ids=main.bot.guild_ids)
    async def clear(self, ctx):
        pass

    @clear.subcommand(name="duplicates",
                      description="Clear duplicated songs from queue.")
    async def clear_dup(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        if main.bot.music_queue[ctx.guild.id]:
            res = []
            [res.append(x) for x in main.bot.music_queue[ctx.guild.id] if x not in res]
            main.bot.music_queue[ctx.guild.id] = res
        embed = nextcord.Embed(title="Duplicated songs cleared! :broom:", color=0x152875)
        embed.set_author(name="Worpal", icon_url="https://i.imgur.com/Rygy2KWs.jpg")
        songs = Play.slist(ctx)
        if songs != "":
            embed.add_field(name="Songs: ", value=songs, inline=True)
        else:
            embed.add_field(name="Songs: ", value="No music in queue", inline=True)
        await ctx.edit_original_message(embed=embed)

    @clear.subcommand(name="all",
                      description="Clear all songs from queue.")
    async def clear_all(self, ctx):
        await ctx.response.send_message('Bot is thinking!')
        if main.bot.music_queue[ctx.guild.id]:
            main.bot.music_queue[ctx.guild.id] = []
        embed = nextcord.Embed(title="Queue cleared! :broom:", color=0x152875)
        await ctx.edit_original_message(embed=embed)


def setup(bot):
    bot.add_cog(Navigation(bot))
