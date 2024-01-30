from discord import ui, Interaction, ButtonStyle, InteractionMessage

from main import Worpal


class EmbedNavigator(ui.View):
    def __init__(self, bot: Worpal, original_interaction: Interaction, page_provider, max_pages: int):
        super().__init__(timeout=180)
        self.bot = bot
        self.original_interaction = original_interaction
        self.page_provider = page_provider
        self.page = 0
        self.max = max_pages

    @ui.button(emoji="⬅️", style=ButtonStyle.grey, disabled=True)
    async def prev(self, interaction: Interaction, button: ui.Button):
        if self.page >= 1:
            self.page -= 1
            for item in self.children:
                if isinstance(item, ui.Button):
                    item.disabled = False

        if self.page <= 0:
            button.disabled = True
            self.page = 0

        await interaction.response.edit_message(embed=self.page_provider.get_page(self.page), view=self)

    @ui.button(emoji="➡️", style=ButtonStyle.grey)
    async def next(self, interaction: Interaction, button: ui.Button):
        if self.page < self.max:
            self.page += 1
            for item in self.children:
                if isinstance(item, ui.Button):
                    item.disabled = False

        if self.page >= self.max:
            button.disabled = True
            self.page = self.max

        await interaction.response.edit_message(embed=self.page_provider.get_page(self.page), view=self)

    @ui.button(emoji="❌", style=ButtonStyle.grey)
    async def delete(self, interaction: Interaction, button: ui.Button):
        self.stop()
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True

        message: InteractionMessage = await self.original_interaction.original_response()
        await message.delete()