"""
Pending command for viewing all users with pending melange payments (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # ['melange_owed', 'owed'] - removed for simplicity
    'description': "View all users with pending melange payments (Admin/Officer only)",
    'permission_level': 'admin_or_officer'
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import get_database, send_response
from utils.base_command import admin_command
from utils.logger import logger


@admin_command('pending')
async def pending(interaction, command_start, use_followup: bool = True):
    """View all users with pending melange payments (Admin only)"""

    try:
        # Get all users with pending melange using utility function
        users_with_pending, get_pending_time = await timed_database_operation(
            "get_all_users_with_pending_melange",
            get_database().get_all_users_with_pending_melange
        )

        if not users_with_pending:
            embed = build_status_embed(
                title="📋 Pending Melange Payments",
                description="✅ **No pending payments!**\n\nAll harvesters have been paid up to date.",
                color=0x00FF00,
                timestamp=interaction.created_at
            )
            await send_response(interaction, embed=embed.build(), use_followup=use_followup)
            return

        # Calculate totals - focus only on melange
        total_melange_owed = sum(user['pending_melange'] for user in users_with_pending)
        total_users = len(users_with_pending)

        # Build user list with melange information only
        user_list = []
        for user_data in users_with_pending:
            username = user_data['username']
            pending_melange = user_data['pending_melange']

            # Format user entry - only show pending melange
            user_list.append(f"• **{username}**: **{pending_melange:,}** melange")

        # Limit display to prevent embed overflow
        max_users_shown = 20
        if len(user_list) > max_users_shown:
            shown_users = user_list[:max_users_shown]
            remaining_count = len(user_list) - max_users_shown
            shown_users.append(f"... and {remaining_count} more user{'s' if remaining_count != 1 else ''}")
            user_list = shown_users

        fields = {
            "👥 Pending Users": "\n".join(user_list) if user_list else "No pending payments"
        }

        # Color based on amount owed
        if total_melange_owed >= 100:
            color = 0xFF4500  # Red - high amount owed
        elif total_melange_owed >= 50:
            color = 0xFFA500  # Orange - moderate amount
        elif total_melange_owed >= 10:
            color = 0xFFD700  # Gold - low amount
        else:
            color = 0x00FF00  # Green - very low amount

        embed = build_status_embed(
            title="📋 Pending Payments",
            description=f"💰 **{total_melange_owed:,} melange** owed to **{total_users}** users",
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
            "Pending Melange",
            str(interaction.user.id),
            interaction.user.display_name,
            total_time,
            admin_id=str(interaction.user.id),
            admin_username=interaction.user.display_name,
            get_pending_time=f"{get_pending_time:.3f}s",
            response_time=f"{response_time:.3f}s",
            users_with_pending=total_users,
            total_melange_owed=total_melange_owed
        )

        # Log the admin request for audit
        logger.info(f"Pending melange report requested by admin {interaction.user.display_name} ({interaction.user.id})",
                   users_pending=total_users, total_melange_owed=total_melange_owed)

    except Exception as error:
        total_time = time.time() - command_start
        logger.error(f"Error in pending command: {error}",
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, "❌ An error occurred while fetching pending payments data.", use_followup=use_followup, ephemeral=True)
