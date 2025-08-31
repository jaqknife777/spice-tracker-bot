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
        # Get all unpaid deposits using utility function
        unpaid_deposits, get_deposits_time = await timed_database_operation(
            "get_all_unpaid_deposits",
            get_database().get_all_unpaid_deposits
        )
        
        if not unpaid_deposits:
            embed = build_status_embed(
                title="📋 Pending Melange Payments",
                description="✅ **No pending payments!**\n\nAll harvesters have been paid up to date.",
                color=0x00FF00,
                footer=f"Requested by {interaction.user.display_name}",
                timestamp=interaction.created_at
            )
            await send_response(interaction, embed=embed.build(), use_followup=use_followup)
            return
        
        # Group deposits by user and calculate totals
        sand_per_melange = get_sand_per_melange()
        user_totals = {}
        total_sand_owed = 0
        total_melange_owed = 0
        
        for deposit in unpaid_deposits:
            user_id = deposit['user_id']
            username = deposit['username']
            sand_amount = deposit['sand_amount']
            
            if user_id not in user_totals:
                user_totals[user_id] = {
                    'username': username,
                    'total_sand': 0,
                    'deposit_count': 0
                }
            
            user_totals[user_id]['total_sand'] += sand_amount
            user_totals[user_id]['deposit_count'] += 1
            total_sand_owed += sand_amount
        
        # Sort users by total sand owed (descending)
        sorted_users = sorted(user_totals.items(), key=lambda x: x[1]['total_sand'], reverse=True)
        
        # Build user list with melange calculations
        user_list = []
        for user_id, user_data in sorted_users:
            username = user_data['username']
            sand_owed = user_data['total_sand']
            melange_owed = sand_owed // sand_per_melange
            deposit_count = user_data['deposit_count']
            
            total_melange_owed += melange_owed
            
            # Format user entry
            deposits_text = f"{deposit_count} deposit{'s' if deposit_count != 1 else ''}"
            user_list.append(f"• **{username}**: {sand_owed:,} sand → **{melange_owed:,} melange** ({deposits_text})")
        
        # Limit display to prevent embed overflow
        max_users_shown = 20
        if len(user_list) > max_users_shown:
            shown_users = user_list[:max_users_shown]
            remaining_count = len(user_list) - max_users_shown
            shown_users.append(f"... and {remaining_count} more user{'s' if remaining_count != 1 else ''}")
            user_list = shown_users
        
        # Calculate summary stats
        remaining_sand = total_sand_owed % sand_per_melange
        sand_ready_for_melange = total_sand_owed - remaining_sand
        
        # Build response embed
        fields = {
            "👥 Users Awaiting Payment": "\n".join(user_list) if user_list else "No users pending payment",
            "📊 Payment Summary": f"**Users:** {len(sorted_users):,}\n"
                                 f"**Total Sand Owed:** {total_sand_owed:,}\n"
                                 f"**Total Melange Owed:** {total_melange_owed:,}\n"
                                 f"**Sand Ready for Melange:** {sand_ready_for_melange:,}\n"
                                 f"**Remaining Sand:** {remaining_sand:,}",
            "⚗️ Conversion Info": f"**Conversion Rate:** {sand_per_melange} sand = 1 melange\n"
                                 f"**Total Deposits:** {len(unpaid_deposits):,}"
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
            description=f"💰 **{total_melange_owed:,} melange** owed across **{len(sorted_users)} user{'s' if len(sorted_users) != 1 else ''}**",
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
            "Pending Payments",
            str(interaction.user.id),
            interaction.user.display_name,
            total_time,
            admin_id=str(interaction.user.id),
            admin_username=interaction.user.display_name,
            get_deposits_time=f"{get_deposits_time:.3f}s",
            response_time=f"{response_time:.3f}s",
            users_with_pending=len(sorted_users),
            total_sand_owed=total_sand_owed,
            total_melange_owed=total_melange_owed,
            total_deposits=len(unpaid_deposits)
        )
        
        # Log the admin request for audit
        logger.info(f"Pending payments report requested by admin {interaction.user.display_name} ({interaction.user.id})", 
                   users_pending=len(sorted_users), total_melange_owed=total_melange_owed)
        
    except Exception as error:
        total_time = time.time() - command_start
        logger.error(f"Error in pending command: {error}", 
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, "❌ An error occurred while fetching pending payments data.", use_followup=use_followup, ephemeral=True)
