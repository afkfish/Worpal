import nextcord
from nextcord import SlashOption
import json
import main
from nextcord.ext import commands


async def settings_embed(ctx):
    embed = nextcord.Embed(title="Settings",
                           description="The setting related to the bot",
                           color=0x152875)
    embed.set_author(name="Worpal",
                     icon_url="https://i.imgur.com/Rygy2KWs.jpg")
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
    await ctx.edit_original_message(embed=embed)


class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="settings",
                            guild_ids=main.bot.guild_ids)
    async def settings_(self, ctx):
        pass

    @settings_.subcommand(name="shuffle_play", description="Turns on/off shuffle playing")
    async def settings_shuffle(self, ctx, shuffle_play: str = SlashOption(name="shuffle_play",
                                                                          description="boolean option",
                                                                          required=True)):
        await ctx.response.send_message('Bot is thinking!')
        print(shuffle_play)
        with open('./settings/settings.json', 'r') as f:
            data = json.load(f)
        if bool(shuffle_play):
            data[str(ctx.guild.id)]['shuffle'] = True
        elif not bool(shuffle_play):
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
        if bool(announce_songs):
            data[str(ctx.guild.id)]['announce'] = True
        elif not bool(announce_songs):
            data[str(ctx.guild.id)]['announce'] = False
        with open('./settings/settings.json', 'w') as f:
            json.dump(data, f, indent=4)
        await settings_embed(ctx)


def setup(bot):
    bot.add_cog(Settings(bot))
