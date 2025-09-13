"""
Treasury command for viewing guild's accumulated resources.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # ['guild_treasury'] - renamed for simplicity
    'description': "View guild treasury balance and statistics",
    'params': {},
    'permission_level': 'admin_or_officer'
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import get_database, get_sand_per_melange, send_response
from utils.base_command import command
from utils.logger import logger


@command('treasury')
async def treasury(interaction, command_start, use_followup: bool = True):
    """View guild treasury balance and statistics"""

    try:
        # Get guild treasury data
        treasury_data, get_treasury_time = await timed_database_operation(
            "get_guild_treasury",
            get_database().get_guild_treasury
        )

        # Get treasury melange (primary currency)
        total_melange = treasury_data.get('total_melange', 0)

        # Format timestamps
        created_at = treasury_data.get('created_at')
        last_updated = treasury_data.get('last_updated')

        created_str = created_at.strftime('%Y-%m-%d %H:%M UTC') if created_at else 'Unknown'
        updated_str = last_updated.strftime('%Y-%m-%d %H:%M UTC') if last_updated else 'Never'

        fields = {
            "💎 Melange": f"**{total_melange:,}** available",
            "📊 Updated": updated_str
        }

        # Determine color based on melange (primary currency)
        if total_melange >= 200:
            color = 0xFFD700  # Gold - very wealthy
        elif total_melange >= 100:
            color = 0x00FF00  # Green - healthy
        elif total_melange >= 50:
            color = 0xFFA500  # Orange - moderate
        else:
            color = 0xFF4500  # Red - low funds

        embed = build_status_embed(
            title="🏛️ Treasury",
            description=f"💎 **{total_melange:,} melange** in treasury",
            color=color,
            fields=fields,
            timestamp=interaction.created_at
        )

        # Send response
        response_start = time.time()
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        response_time = time.time() - response_start

        # Log metrics
        total_time = time.time() - command_start
        log_command_metrics(
            "Guild Treasury",
            str(interaction.user.id),
            interaction.user.display_name,
            total_time,
            get_treasury_time=f"{get_treasury_time:.3f}s",
            response_time=f"{response_time:.3f}s",
            total_melange=total_melange
        )

    except Exception as error:
        total_time = time.time() - command_start
        from utils.logger import logger
        logger.error(f"Error in treasury command: {error}",
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, "❌ An error occurred while fetching guild treasury data.", use_followup=use_followup, ephemeral=True)
