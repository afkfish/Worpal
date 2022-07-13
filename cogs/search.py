import datetime as dt

import nextcord
from nextcord import slash_command, SlashOption, Embed, utils
from nextcord.ext import commands

import main
from cogs.play import Play
from utils.song_info import search_yt


class Confirm(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @nextcord.ui.button(label="1", style=nextcord.ButtonStyle.grey)
    async def first(self, button: nextcord.ui.Button, ctx):
        await ctx.response.send_message("Playing 1.", ephemeral=True)
        self.value = 1
        self.stop()

    @nextcord.ui.button(label="2", style=nextcord.ButtonStyle.grey)
    async def second(self, button: nextcord.ui.Button, ctx):
        await ctx.response.send_message("Playing 2.", ephemeral=True)
        self.value = 2
        self.stop()

    @nextcord.ui.button(label="3", style=nextcord.ButtonStyle.grey)
    async def third(self, button: nextcord.ui.Button, ctx):
        await ctx.response.send_message("Playing 3.", ephemeral=True)
        self.value = 3
        self.stop()

    @nextcord.ui.button(label="4", style=nextcord.ButtonStyle.grey)
    async def fourth(self, button: nextcord.ui.Button, ctx):
        await ctx.response.send_message("Playing 4.", ephemeral=True)
        self.value = 4
        self.stop()

    @nextcord.ui.button(label="5", style=nextcord.ButtonStyle.grey)
    async def fifth(self, button: nextcord.ui.Button, ctx):
        await ctx.response.send_message("Playing 5.", ephemeral=True)
        self.value = 5
        self.stop()


class Search(commands.Cog):
    def __int__(self, bot):
        self.bot = bot

    @slash_command(name="search",
                   description="Search for a song on youtube.",
                   guild_ids=main.bot.guild_ids)
    async def search_(self, ctx, q: str = SlashOption(name="title",
                                                      description="The video to be found.",
                                                      required=True)):
        await ctx.response.send_message('The bot is thinking...')
        songs = search_yt(q, True)
        view = Confirm()
        embed = Embed(title=f"Search results for {q}", color=0x152875)
        embed.set_author(name="Worpal", icon_url=main.icon)
        cropped = [{'source': song['formats'][0]['url'], 'title': song['title'], 'thumbnail': song['thumbnail'],
                    'duration': song['duration']} for song in songs]
        if len(cropped) > 0:
            a = ""
            i = 0
            for i, entry in enumerate(cropped, i):
                a += f"{i + 1}. {entry['title']}\n"
            embed.add_field(name="Results:", value=a)
            await ctx.edit_original_message(embed=embed, view=view)
            await view.wait()
            if ctx.user.voice:
                voice = utils.get(main.bot.voice_clients, guild=ctx.guild)
                voice_channel = ctx.user.voice.channel
                if view.value is not None:
                    main.bot.music_queue[ctx.guild.id].append([cropped[view.value-1], voice_channel])
                    embed = Embed(title="Song added from search", color=0x152875)
                    embed.set_thumbnail(url=main.bot.music_queue[ctx.guild.id][-1][0]['thumbnail'])
                    embed.add_field(name=main.bot.music_queue[ctx.guild.id][-1][0]['title'],
                                    value=str(dt.timedelta(
                                        seconds=int(main.bot.music_queue[ctx.guild.id][-1][0]['duration']))),
                                    inline=True)
                    embed.set_footer(text="Song requested by: " + ctx.user.name)
                    await ctx.send(embed=embed)
                    if not voice.is_playing():
                        await Play(commands.Cog).play_music(ctx, voice)

        else:
            await ctx.edit_original_message(content="Error in getting the videos!")


def setup(bot):
    bot.add_cog(Search(bot))
