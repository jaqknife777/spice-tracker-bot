"""
Refinery command for viewing spice refinery statistics and progress.
"""

import time
from utils.database_utils import get_user_stats
from utils.embed_utils import build_info_embed, build_progress_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, get_sand_per_melange, send_response

# Command metadata
COMMAND_METADATA = {
    'aliases': ['status'],
    'description': "View your spice refinery statistics and progress"
}


@handle_interaction_expiration
async def refinery(interaction, use_followup: bool):
    """Show your total sand and melange statistics"""
    command_start = time.time()

    # Use utility function for database operations
    user_stats = await get_user_stats(get_database(), str(interaction.user.id))

    if not user_stats['user'] and user_stats['total_sand'] == 0:
        embed = build_info_embed(
            title="🏭 Spice Refinery Status",
            info_message="🏜️ You haven't harvested any spice sand yet! Use `/harvest` to start tracking your harvests.",
            color=0x95A5A6,
            footer=f"Requested by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup, ephemeral=True)
        return

    # Calculate progress and melange status
    sand_per_melange = get_sand_per_melange()
    remaining_sand = user_stats['total_sand'] % sand_per_melange

    # Build progress fields
    last_activity_timestamp = (
        user_stats['user']['last_updated'].timestamp()
        if user_stats['user'] else interaction.created_at.timestamp()
    )

    progress_fields = {
        "🏜️ Harvest Summary": f"**Total Sand Collected:** {user_stats['total_sand']:,}",
        "💰 Melange Status": (
            f"**Total Melange Earned:** {user_stats['total_melange']:,}\n"
            f"**Pending Payment:** {user_stats['pending_melange']:,}\n"
            f"**Already Paid:** {user_stats['paid_melange']:,}"
        ),
        "✨ Production Progress": (
            f"**Sand Ready for Melange:** {user_stats['total_sand'] - remaining_sand:,}\n"
            f"**Remaining Sand:** {remaining_sand:,}"
        ),
        "⚙️ Refinement Rate": f"{sand_per_melange} sand = 1 melange",
        "📅 Last Activity": f"<t:{int(last_activity_timestamp)}:F>"
    }

    # Use utility function for progress embed
    embed = build_progress_embed(
        title="🏭 Spice Refinery Status",
        current=remaining_sand,
        total=sand_per_melange,
        progress_fields=progress_fields,
        footer=f"Spice Refinery • {interaction.user.display_name}",
        thumbnail=interaction.user.display_avatar.url,
        timestamp=interaction.created_at
    )

    # Send response using helper function (ephemeral for privacy)
    response_start = time.time()
    await send_response(interaction, embed=embed.build(), use_followup=use_followup, ephemeral=True)
    response_time = time.time() - response_start

    # Log performance metrics using utility function
    total_time = time.time() - command_start
    log_command_metrics(
        "Refinery",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        **user_stats['timing'],
        response_time=f"{response_time:.3f}s",
        total_sand=user_stats['total_sand'],
        total_melange=user_stats['total_melange'],
        pending_melange=user_stats['pending_melange'],
        paid_melange=user_stats['paid_melange'],
        sand_ready=user_stats['total_sand'] - remaining_sand
    )
