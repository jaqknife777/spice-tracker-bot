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
    
    # Pay all users their pending melange
    payroll_result, payroll_time = await timed_database_operation(
        "pay_all_pending_melange",
        get_database().pay_all_pending_melange,
        str(interaction.user.id), interaction.user.display_name
    )
    
    total_paid = payroll_result.get('total_paid', 0)
    users_paid = payroll_result.get('users_paid', 0)
    
    if users_paid == 0:
        embed = build_status_embed(
            title="💰 Payroll Status",
            description="🏜️ There are no users with pending melange to pay.",
            color=0x95A5A6,
            footer=f"Requested by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        return
    
    # Use utility function for embed building
    fields = {
        "💰 Payroll Summary": f"**Total Melange Paid:** {total_paid:,}\n**Users Paid:** {users_paid}"
    }
    
    embed = build_status_embed(
        title="💰 Guild Payroll Complete",
        description="**All users with pending melange have been paid!**",
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
        "Melange Payroll",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        admin_id=str(interaction.user.id),
        admin_username=interaction.user.display_name,
        payroll_time=f"{payroll_time:.3f}s",
        response_time=f"{response_time:.3f}s",
        melange_paid=total_paid,
        users_paid=users_paid
    )
    
    print(f'Payroll processed by {interaction.user.display_name} ({interaction.user.id}) - {users_paid} users paid {total_paid:,} melange')
