from discord import Embed, Interaction, app_commands
from discord.ext import commands

from main import Worpal

bool_str = ["1", "true", "yes", "y", "t"]


async def settings_embed(bot: Worpal, interaction: Interaction):
    embed = Embed(title="Settings",
                  description="The setting related to the bot",
                  color=bot.color)
    embed.set_author(name="Worpal", icon_url=bot.icon)
    embed.add_field(name="Shuffle play :twisted_rightwards_arrows:",
                    value="Plays the songs shuffled\n\nEnabled: {}".format(
                        "True :white_check_mark:" if bot.shuffle(interaction.guild.id) else "False :x:"
                    ),
                    inline=True)
    embed.add_field(name="Announce songs :mega:",
                    value="Songs will be announced when played\n\nEnabled: {}".format(
                        "True :white_check_mark:" if bot.announce(interaction.guild.id) else "False :x:"
                    ),
                    inline=True)
    embed.add_field(name="Loop songs :repeat:",
                    value="The current song will loop while the setting is true\n\nEnabled: {}".format(
                        "True :white_check_mark:" if bot.looping(interaction.guild.id) else "False :x:"
                    ),
                    inline=True)
    await interaction.followup.send(embed=embed)


class Settings(commands.GroupCog, name="settings"):
    def __init__(self, bot: Worpal):
        self.bot = bot

    @app_commands.command(name="shuffle_play", description="Turns on/off shuffle playing")
    async def settings_shuffle(self, interaction: Interaction, shuffle_play: str):
        await interaction.response.defer()
        if shuffle_play.lower() in bool_str:
            self.bot.settings[str(interaction.guild.id)]['shuffle'] = True
        else:
            self.bot.settings[str(interaction.guild.id)]['shuffle'] = False
        await settings_embed(self.bot, interaction)

    @app_commands.command(name="announce_songs", description="Turns on/off announce")
    async def settings_announce(self, interaction: Interaction, announce_songs: str):
        await interaction.response.defer()
        if announce_songs.lower() in bool_str:
            self.bot.settings[str(interaction.guild.id)]['announce'] = True
        else:
            self.bot.settings[str(interaction.guild.id)]['announce'] = False
        await settings_embed(self.bot, interaction)

    # @app_commands.command(name="loop", description="Turns on/off loop")
    # async def settigs_loop(self, interaction: Interaction, loop: str):
    # 	await interaction.response.defer()
    # 	if loop.lower() in bool_str:
    # 		self.bot.settings[str(interaction.guild.id)]['loop'] = True
    # 	else:
    # 		self.bot.settings[str(interaction.guild.id)]['loop'] = False
    # 	await settings_embed(self.bot, interaction)


async def setup(bot):
    await bot.add_cog(Settings(bot))
