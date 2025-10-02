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
import discord
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import get_database, send_response
from utils.base_command import admin_command
from utils.logger import logger
from views import ConfirmView


@admin_command('reset')
async def reset(interaction: discord.Interaction, command_start: float, confirm: bool, use_followup: bool = True):
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

    async def on_confirm():
        # Acknowledge the button click
        await interaction.followup.send("Processing reset...", ephemeral=True)

        # Reset all refinery statistics using utility function
        deleted_rows, reset_time = await timed_database_operation(
            "reset_all_stats",
            get_database().reset_all_stats
        )

        # Use utility function for embed building
        fields = {
            "📊 Reset Summary": f"**Users Affected:** {deleted_rows}\n**Data Cleared:** All harvest records and melange production",
            "✅ What Remains": "Refinement rates are preserved."
        }

        embed = build_status_embed(
            title="🔄 Refinery Reset Complete",
            description="**All refinery statistics have been permanently deleted!**",
            color=0xE74C3C,
            fields=fields,
            timestamp=interaction.created_at
        )

        # Edit the original message with the result
        await interaction.edit_original_response(embed=embed.build(), view=None)

        # Log performance metrics
        total_time = time.time() - command_start
        log_command_metrics(
            "Reset",
            str(interaction.user.id),
            interaction.user.display_name,
            total_time,
            admin_id=str(interaction.user.id),
            admin_username=interaction.user.display_name,
            reset_time=f"{reset_time:.3f}s",
            deleted_rows=deleted_rows
        )
        logger.info(f'All refinery statistics reset by {interaction.user.display_name} ({interaction.user.id}) - {deleted_rows} records deleted',
                    admin_id=str(interaction.user.id), admin_username=interaction.user.display_name,
                    deleted_rows=deleted_rows)

    async def on_cancel():
        embed = build_status_embed(
            title="🚫 Reset Cancelled",
            description="The reset operation was cancelled. No data has been changed.",
            color=0x95A5A6,
            timestamp=interaction.created_at
        )
        await interaction.edit_original_response(embed=embed.build(), view=None)

    view = ConfirmView(on_confirm=on_confirm, on_cancel=on_cancel)

    embed = build_status_embed(
        title="🚨 ARE YOU SURE? 🚨",
        description=(
            "This is your final confirmation. Clicking **Confirm** will **permanently delete all user data**, "
            "including harvest records, melange balances, and pending amounts. "
            "**This action is irreversible.**"
        ),
        color=0xE74C3C,
        fields={"🛑 To Proceed": "Click the **Confirm** button below.", "🔙 To Cancel": "Click the **Cancel** button."},
        timestamp=interaction.created_at
    )

    await send_response(interaction, embed=embed.build(), view=view, use_followup=use_followup, ephemeral=True)

    # Wait for the view to stop (timeout or button click)
    await view.wait()
    if not view.is_finished():
        # Timeout logic
        timeout_embed = build_status_embed(
            title="⌛ Reset Timed Out",
            description="The reset confirmation timed out. No data has been changed.",
            color=0x95A5A6,
            timestamp=interaction.created_at
        )
        await interaction.edit_original_response(embed=timeout_embed.build(), view=None)