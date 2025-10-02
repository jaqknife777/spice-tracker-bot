import discord
from typing import Callable, Awaitable

class ConfirmView(discord.ui.View):
    def __init__(self, on_confirm: Callable[[], Awaitable[None]], on_cancel: Callable[[], Awaitable[None]]):
        super().__init__(timeout=60)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.on_confirm()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.on_cancel()
        self.stop()