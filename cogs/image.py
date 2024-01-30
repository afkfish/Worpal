from discord import app_commands, Interaction, Embed
from discord.ext import commands

from api.Unsplash import search
from cogs.helper.paged_embed import EmbedNavigator
from main import Worpal


class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.images = []
        self.query = ""
        self.view = None

    @app_commands.command(name="image", description="get an image by a query")
    async def image(self, interaction: Interaction, query: str):
        await interaction.response.defer()
        if self.view:
            self.view.stop()
        self.query = query
        self.images = search(query)
        self.view = EmbedNavigator(self.bot, interaction, self, len(self.images) - 1)
        embed = self.get_page(0)
        await interaction.followup.send(embed=embed, view=self.view)
        await self.view.wait()
        embed = self.get_page(self.view.page)
        await interaction.edit_original_response(embed=embed, view=None)

    def get_page(self, page: int) -> Embed:
        embed = Embed(title=f"Images for: {self.query}", color=Worpal.color)
        embed.set_footer(text=f"Page {page + 1}/10")

        embed.set_image(url=self.images[page])
        return embed


async def setup(bot):
    await bot.add_cog(Image(bot))
