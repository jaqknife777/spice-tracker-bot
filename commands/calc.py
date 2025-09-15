"""
Calc command for estimating melange from a sand deposit without persisting data.
Public command: anyone can use it. Does not modify the database.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],
    'description': "Estimate melange from a sand deposit (no database update)",
    'params': {'amount': "Amount of spice sand to calculate"},
    'permission_level': 'any'
}

from utils.base_command import command
from utils.embed_utils import build_status_embed
from utils.helpers import convert_sand_to_melange, get_sand_per_melange_with_bonus, send_response


@command('calc')
async def calc(interaction, command_start, amount: int, use_followup: bool = True):
    """Calculate melange from a sand amount using the current conversion rate.

    This command does not write anything to the database. It only reports the
    expected melange yield and leftover sand at the current conversion rate.

    Args:
        interaction: The Discord interaction context.
        command_start: Start time injected by the base command decorator.
        amount: The amount of spice sand to calculate.
        use_followup: Whether to use interaction.followup.send.
    """

    # Validate amount: must be at least 1, no upper limit
    if amount < 1:
        await send_response(
            interaction,
            "❌ Amount must be at least 1 spice sand.",
            use_followup=use_followup,
            ephemeral=True,
        )
        return

    # Get current conversion rate (accounts for landsraad bonus if active)
    conversion_rate = await get_sand_per_melange_with_bonus()

    # Calculate projected melange and remaining sand
    melange_amount, remaining_sand = await convert_sand_to_melange(amount)

    description = (
        f"Calculating for {amount:,} spice sand at a rate of "
        f"{conversion_rate:g} sand → 1 melange.\n\n"
        f"You would receive: **{melange_amount:,} melange**\n"
        f"Leftover sand: **{remaining_sand:,}**"
    )

    embed = build_status_embed(
        title="Sand → Melange Calculator",
        description=description,
        color=0x3498DB,
    )

    await send_response(interaction, embed=embed, use_followup=use_followup)
