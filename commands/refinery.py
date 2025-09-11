"""
Refinery command for viewing spice refinery statistics and progress.
"""

import time
from utils.database_utils import validate_user_exists
from utils.embed_utils import build_info_embed, build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, send_response

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # ['status'] - removed for simplicity
    'description': "View your melange production and payment status"
}


@handle_interaction_expiration
async def refinery(interaction, use_followup: bool = True):
    """Show your melange production statistics"""
    command_start = time.time()

    # Get user data directly from database
    user = await validate_user_exists(get_database(), str(interaction.user.id), interaction.user.display_name, create_if_missing=False)

    if not user or user.get('total_melange', 0) == 0:
        embed = build_info_embed(
            title="🏭 Spice Refinery Status",
            info_message="💎 You haven't produced any melange yet! Use `/sand` to convert spice sand into melange.",
            color=0x95A5A6,
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup, ephemeral=True)
        return

    # Build melange status fields
    last_updated = user.get('last_updated') if user else None
    if last_updated:
        # Handle both datetime objects and integer timestamps
        if hasattr(last_updated, 'timestamp'):
            # It's a datetime object
            last_activity_timestamp = last_updated.timestamp()
        elif isinstance(last_updated, (int, float)):
            # It's already a Unix timestamp
            last_activity_timestamp = float(last_updated)
        else:
            # Fallback to current time
            last_activity_timestamp = interaction.created_at.timestamp()
    else:
        last_activity_timestamp = interaction.created_at.timestamp()

    # Calculate pending melange
    total_melange = user.get('total_melange', 0)
    paid_melange = user.get('paid_melange', 0)
    pending_melange = total_melange - paid_melange

    fields = {
        "💎 Melange": f"**{total_melange:,}** total | **{pending_melange:,}** pending | **{paid_melange:,}** paid",
        "💰 Activity": f"<t:{int(last_activity_timestamp)}:R>"
    }

    embed = build_status_embed(
        title="🏭 Refinery Status",
        description=f"💎 **{total_melange:,} melange** produced",
        color=0xF39C12,
        fields=fields,
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
        response_time=f"{response_time:.3f}s",
        total_melange=total_melange,
        pending_melange=pending_melange,
        paid_melange=paid_melange
    )
