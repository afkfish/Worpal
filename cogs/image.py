from discord import app_commands, Interaction, ui, ButtonStyle, Embed
from discord.ext import commands

from api.Unsplash import search
from cogs.helper.paged_embed import EmbedNavigator
from main import Worpal


class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.images = []
        self.query = ""

    @app_commands.command(name="image", description="get an image by a query")
    async def image(self, interaction: Interaction, query: str):
        await interaction.response.defer()
        self.query = query
        self.images = search(query)
        view = EmbedNavigator(self.bot, interaction, self, len(self.images) - 1)
        embed = self.get_page(0)
        await interaction.followup.send(embed=embed, view=view)
        await view.wait()

    def get_page(self, page: int) -> Embed:
        embed = Embed(title=f"Images for: {self.query}", color=Worpal.color)
        embed.set_footer(text=f"Page {page + 1}/10")

        embed.set_image(url=self.images[page])
        return embed


async def setup(bot):
    await bot.add_cog(Image(bot))
