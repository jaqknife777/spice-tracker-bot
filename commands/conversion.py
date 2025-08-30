"""
Conversion command for viewing the current spice sand to melange conversion rate.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['rate'],
    'description': "View the current spice sand to melange conversion rate"
}

import time
from utils.embed_utils import build_status_embed
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_sand_per_melange, send_response
from utils.logger import logger


@handle_interaction_expiration
async def conversion(interaction, use_followup: bool = True):
    """View the current spice sand to melange conversion rate"""
    try:
        # Get current rate from environment
        current_rate = get_sand_per_melange()
        
        # Use utility function for embed building
        fields = {
            "📊 Current Rate": f"**{current_rate} sand = 1 melange**",
            "⚠️ Important Note": "The conversion rate is set via environment variables and cannot be changed through commands. Contact an administrator to modify the SAND_PER_MELANGE environment variable."
        }
        
        embed = build_status_embed(
            title="⚙️ Refinement Rate Information",
            description="Current spice sand to melange conversion rate",
            color=0x3498DB,
            fields=fields,
            footer=f"Requested by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        print(f'Refinement rate info requested by {interaction.user.display_name} ({interaction.user.id}) - Current rate: {current_rate}')
        
    except Exception as error:
        logger.error(f"Error in conversion command: {error}")
        await send_response(interaction, "❌ An error occurred while fetching the refinement rate.", use_followup=use_followup, ephemeral=True)
