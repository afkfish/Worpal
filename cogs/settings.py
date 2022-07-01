import json

from nextcord import SlashOption, slash_command, Embed
from nextcord.ext import commands

import main

bool_str = ["1", "true", "yes", "y", "t"]


async def settings_embed(ctx):
    embed = Embed(title="Settings",
                  description="The setting related to the bot",
                  color=0x152875)
    embed.set_author(name="Worpal",
                     icon_url=main.icon)
    embed.add_field(name="Prefix",
                    value="Currently the prefix is not changable due to lack of "
                          "knowledge the developer has",
                    inline=False)
    embed.add_field(name="Shuffle play :twisted_rightwards_arrows:",
                    value="Plays the songs shuffled\n\nEnabled: {}".format(
                        "True :white_check_mark:" if main.bot_shuffle(ctx.guild.id) else "False :x:"
                    ),
                    inline=True)
    embed.add_field(name="Announce songs :mega:",
                    value="Songs will be announced when played\n\nEnabled: {}".format(
                        "True :white_check_mark:" if main.bot_announce(ctx.guild.id) else "False :x:"
                    ),
                    inline=True)
    embed.add_field(name="Loop songs :repeat:",
                    value="The current song will loop while the setting is true\n\nEnabled: {}".format(
                        "True :white_check_mark:" if main.bot_loop(ctx.guild.id) else "False :x:"
                    ),
                    inline=True)
    await ctx.edit_original_message(embed=embed)


class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="settings",
                   guild_ids=main.bot.guild_ids)
    async def settings_(self, ctx):
        pass

    @settings_.subcommand(name="shuffle_play", description="Turns on/off shuffle playing")
    async def settings_shuffle(self, ctx, shuffle_play: str = SlashOption(name="shuffle_play",
                                                                          description="boolean option",
                                                                          required=True)):
        await ctx.response.send_message('Bot is thinking!')
        with open('./settings/settings.json', 'r') as f:
            data = json.load(f)
        if shuffle_play.lower() in bool_str:
            data[str(ctx.guild.id)]['shuffle'] = True
        else:
            data[str(ctx.guild.id)]['shuffle'] = False
        with open('./settings/settings.json', 'w') as f:
            json.dump(data, f, indent=4)
        await settings_embed(ctx)

    @settings_.subcommand(name="announce_songs", description="Turns on/off announce")
    async def settings_announce(self, ctx, announce_songs: str = SlashOption(name="announce_songs",
                                                                             description="boolean option",
                                                                             required=True)):
        await ctx.response.send_message('Bot is thinking!')
        with open('./settings/settings.json', 'r') as f:
            data = json.load(f)
        if announce_songs.lower() in bool_str:
            data[str(ctx.guild.id)]['announce'] = True
        else:
            data[str(ctx.guild.id)]['announce'] = False
        with open('./settings/settings.json', 'w') as f:
            json.dump(data, f, indent=4)
        await settings_embed(ctx)

    @settings_.subcommand(name="loop", description="Turns on/off loop")
    async def settigs_loop(self, ctx, loop: str = SlashOption(name="loop",
                                                              description="boolean option",
                                                              required=True)):
        await ctx.response.send_message('Bot is thinking!')
        with open('./settings/settings.json', 'r') as f:
            data = json.load(f)
        if loop.lower() in bool_str:
            data[str(ctx.guild.id)]['loop'] = True
        else:
            data[str(ctx.guild.id)]['loop'] = False
        with open('./settings/settings.json', 'w') as f:
            json.dump(data, f, indent=4)
        await settings_embed(ctx)


def setup(bot):
    bot.add_cog(Settings(bot))
