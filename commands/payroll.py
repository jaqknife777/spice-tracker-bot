"""
Payroll command for processing payments for all unpaid harvesters (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['payall'],
    'description': "Process payments for all unpaid harvesters (Admin only)"
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, send_response
from utils.permissions import is_admin


@handle_interaction_expiration
async def payroll(interaction, use_followup: bool = True):
    """Process payments for all unpaid harvesters (Admin only)"""
    command_start = time.time()
    
    # Check if user has admin permissions
    if not is_admin(interaction):
        await send_response(interaction, "❌ You need an admin role to use this command. Contact a server administrator.", use_followup=use_followup, ephemeral=True)
        return
    
    # Get all unpaid deposits using utility function
    unpaid_deposits, get_deposits_time = await timed_database_operation(
        "get_all_unpaid_deposits",
        get_database().get_all_unpaid_deposits
    )
    
    if not unpaid_deposits:
        embed = build_status_embed(
            title="💰 Payroll Status",
            description="🏜️ There are no unpaid harvests to process.",
            color=0x95A5A6,
            footer=f"Requested by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        return
    
    # Group deposits by user
    user_deposits = {}
    for deposit in unpaid_deposits:
        user_id = deposit['user_id']
        if user_id not in user_deposits:
            user_deposits[user_id] = []
        user_deposits[user_id].append(deposit)
    
    # Mark all deposits as paid using utility function
    total_paid = 0
    users_paid = 0
    
    for user_id, deposits_list in user_deposits.items():
        _, update_time = await timed_database_operation(
            "mark_all_user_deposits_paid",
            get_database().mark_all_user_deposits_paid,
            user_id
        )
        user_total = sum(deposit['sand_amount'] for deposit in deposits_list)
        total_paid += user_total
        users_paid += 1
    
    # Use utility function for embed building
    fields = {
        "📊 Payroll Summary": f"**Total Spice Sand Paid:** {total_paid:,}\n**Harvesters Paid:** {users_paid}\n**Total Harvests:** {len(unpaid_deposits)}"
    }
    
    embed = build_status_embed(
        title="💰 Guild Payroll Complete",
        description="**All harvesters have been paid for their harvests!**",
        color=0x27AE60,
        fields=fields,
        footer=f"Guild payroll processed by {interaction.user.display_name}",
        timestamp=interaction.created_at
    )
    
    # Send response using helper function
    response_start = time.time()
    await send_response(interaction, embed=embed.build(), use_followup=use_followup)
    response_time = time.time() - response_start
    
    # Log performance metrics using utility function
    total_time = time.time() - command_start
    log_command_metrics(
        "Payroll",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        admin_id=str(interaction.user.id),
        admin_username=interaction.user.display_name,
        get_deposits_time=f"{get_deposits_time:.3f}s",
        response_time=f"{response_time:.3f}s",
        total_paid=total_paid,
        users_paid=users_paid,
        total_harvests=len(unpaid_deposits)
    )
    
    print(f'Guild payroll of {total_paid:,} spice sand to {interaction.user.display_name} ({interaction.user.id})')
