"""
Reset command for resetting all spice refinery statistics (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],
    'description': "Reset all spice refinery statistics (Admin only - USE WITH CAUTION)",
    'params': {'confirm': "Confirm that you want to delete all refinery data"}
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_warning_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, send_response
from utils.logger import logger


@handle_interaction_expiration
async def reset(interaction, confirm: bool, use_followup: bool = True):
    """Reset all spice refinery statistics (Admin only - USE WITH CAUTION)"""
    command_start = time.time()
    
    try:
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await send_response(interaction, "❌ You need administrator permissions to use this command.", use_followup=use_followup, ephemeral=True)
            return
        
        if not confirm:
            embed = build_warning_embed(
                title="⚠️ Reset Cancelled",
                warning_message="You must set the `confirm` parameter to `True` to proceed with the reset.",
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
        
        embed = build_warning_embed(
            title="🔄 Refinery Reset Complete",
            warning_message="**All refinery statistics have been permanently deleted!**",
            fields=fields,
            footer=f"Reset performed by {interaction.user.display_name}",
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
        
        print(f'All refinery statistics reset by {interaction.user.display_name} ({interaction.user.id}) - {deleted_rows} records deleted')
        
    except Exception as error:
        total_time = time.time() - command_start
        logger.error(f"Error in reset command: {error}", 
                    admin_id=str(interaction.user.id),
                    admin_username=interaction.user.display_name,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, "❌ An error occurred while resetting refinery statistics.", use_followup=use_followup, ephemeral=True)
