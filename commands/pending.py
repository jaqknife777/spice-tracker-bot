"""
Pending command for viewing all users with pending melange payments (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['melange_owed', 'owed'],
    'description': "View all users with pending melange payments (Admin only)"
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, get_sand_per_melange, send_response
from utils.permissions import is_admin
from utils.logger import logger


@handle_interaction_expiration
async def pending(interaction, use_followup: bool = True):
    """View all users with pending melange payments (Admin only)"""
    command_start = time.time()
    
    # Check if user has admin permissions
    if not is_admin(interaction):
        await send_response(interaction, "❌ You need an admin role to use this command. Contact a server administrator.", use_followup=use_followup, ephemeral=True)
        return
    
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
                footer=f"Requested by {interaction.user.display_name}",
                timestamp=interaction.created_at
            )
            await send_response(interaction, embed=embed.build(), use_followup=use_followup)
            return
        
        # Calculate totals
        total_melange_owed = sum(user['pending_melange'] for user in users_with_pending)
        total_sand = sum(user['total_sand'] for user in users_with_pending)
        total_users = len(users_with_pending)
        
        # Build user list with melange information
        user_list = []
        for user_data in users_with_pending:
            username = user_data['username']
            pending_melange = user_data['pending_melange']
            total_sand_user = user_data['total_sand']
            deposit_count = user_data['total_deposits']
            
            # Format user entry
            deposits_text = f"{deposit_count} deposit{'s' if deposit_count != 1 else ''}"
            user_list.append(f"• **{username}**: {total_sand_user:,} sand → **{pending_melange:,} melange** ({deposits_text})")
        
        # Limit display to prevent embed overflow
        max_users_shown = 20
        if len(user_list) > max_users_shown:
            shown_users = user_list[:max_users_shown]
            remaining_count = len(user_list) - max_users_shown
            shown_users.append(f"... and {remaining_count} more user{'s' if remaining_count != 1 else ''}")
            user_list = shown_users
        
        # Build response embed
        fields = {
            "👥 Users Awaiting Payment": "\n".join(user_list) if user_list else "No users pending payment",
            "💰 Payment Summary": f"**Users with Pending Melange:** {total_users:,}\n"
                                 f"**Total Sand Collected:** {total_sand:,}\n"
                                 f"**Total Melange Owed:** {total_melange_owed:,}",
            "📊 Additional Info": f"**Total Deposits:** {sum(user['total_deposits'] for user in users_with_pending):,}"
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
            title="📋 Guild Pending Melange Payments",
            description=f"💰 **{total_melange_owed:,} melange** owed across **{total_users} user{'s' if total_users != 1 else ''}**",
            color=color,
            fields=fields,
            footer=f"Admin Report • Requested by {interaction.user.display_name}",
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
            total_sand=total_sand,
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
