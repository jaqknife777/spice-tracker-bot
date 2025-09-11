"""
Reset command for resetting all spice refinery statistics (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],
    'description': "Reset all spice refinery statistics (Admin only - USE WITH CAUTION)",
    'params': {'confirm': "Confirm that you want to delete all refinery data"},
    'permission_level': 'admin'
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import get_database, send_response
from utils.base_command import admin_command
from utils.logger import logger


@admin_command('reset')
async def reset(interaction, command_start, confirm: bool, use_followup: bool = True):
    """Reset all spice refinery statistics (Admin only - USE WITH CAUTION)"""

    if not confirm:
        embed = build_status_embed(
            title="⚠️ Reset Cancelled",
            description="You must set the `confirm` parameter to `True` to proceed with the reset.",
            color=0xF39C12,
            fields={"🔄 How to Reset": "Use `/reset confirm:True` to confirm the reset."},
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup, ephemeral=True)
        return

    # Reset all refinery statistics using utility function
    deleted_rows, reset_time = await timed_database_operation(
        "reset_all_stats",
        get_database().reset_all_stats
    )

    # Use utility function for embed building
    fields = {
        "📊 Reset Summary": f"**Users Affected:** {deleted_rows}\n**Data Cleared:** All harvest records and melange production",
        "✅ What Remains": "Refinement rates and bot settings are preserved."
    }

    embed = build_status_embed(
        title="🔄 Refinery Reset Complete",
        description="**All refinery statistics have been permanently deleted!**",
        color=0xF39C12,
        fields=fields,
        timestamp=interaction.created_at
    )

    # Send response using helper function
    response_start = time.time()
    await send_response(interaction, embed=embed.build(), use_followup=use_followup)
    response_time = time.time() - response_start

    # Log performance metrics using utility function
    total_time = time.time() - command_start
    log_command_metrics(
        "Reset",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        admin_id=str(interaction.user.id),
        admin_username=interaction.user.display_name,
        reset_time=f"{reset_time:.3f}s",
        response_time=f"{response_time:.3f}s",
        deleted_rows=deleted_rows
    )

    logger.info(f'All refinery statistics reset by {interaction.user.display_name} ({interaction.user.id}) - {deleted_rows} records deleted',
                admin_id=str(interaction.user.id), admin_username=interaction.user.display_name,
                deleted_rows=deleted_rows)
