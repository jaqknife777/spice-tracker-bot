"""
Leaderboard command for displaying top spice refiners by melange production.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # ['top'] - removed for simplicity
    'description': "Display top spice refiners by melange production",
    'params': {'limit': "Number of top refiners to display (default: 10)"},
    'permission_level': 'user'
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_info_embed, build_leaderboard_embed
from utils.command_utils import log_command_metrics
from utils.base_command import command
from utils.helpers import get_database, send_response


@command('leaderboard')
async def leaderboard(interaction, command_start, limit: int = 10, use_followup: bool = True):
    """Display top refiners by melange earned"""

    # Validate limit
    if not 5 <= limit <= 25:
        await send_response(interaction, "❌ Limit must be between 5 and 25.", use_followup=use_followup, ephemeral=True)
        return

    # Database operation with timing using utility function
    leaderboard_data, get_leaderboard_time = await timed_database_operation(
        "get_leaderboard",
        get_database().get_leaderboard,
        limit
    )

    if not leaderboard_data:
        embed = build_info_embed(
            title="🏆 Spice Refinery Rankings",
            info_message="🏜️ No refiners found yet! Be the first to start harvesting spice sand with `/sand`.",
            color=0x95A5A6,
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        return

    # Calculate totals - focus on melange as primary currency
    total_melange = sum(user['total_melange'] for user in leaderboard_data)

    # Use utility function for leaderboard embed
    total_stats = {
        'total_refiners': len(leaderboard_data),
        'total_melange': total_melange
    }

    embed = build_leaderboard_embed(
        title="🏆 Spice Refinery Rankings",
        leaderboard_data=leaderboard_data,
        total_stats=total_stats,
        timestamp=interaction.created_at
    )

    # Send response using helper function
    response_start = time.time()
    await send_response(interaction, embed=embed.build(), use_followup=use_followup)
    response_time = time.time() - response_start

    # Log performance metrics using utility function
    total_time = time.time() - command_start
    log_command_metrics(
        "Leaderboard",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        limit=limit,
        get_leaderboard_time=f"{get_leaderboard_time:.3f}s",
        response_time=f"{response_time:.3f}s",
        result_count=len(leaderboard_data),
        total_melange=total_melange
    )
