"""
Payroll command for processing payments for all unpaid harvesters (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # ['payall'] - removed for simplicity
    'description': "Process payments for all unpaid harvesters (Admin only)",
    'permission_level': 'admin'
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import get_database, send_response
from utils.base_command import admin_command
from utils.logger import logger


@admin_command('payroll')
async def payroll(interaction, command_start, use_followup: bool = True):
    """Process payments for all unpaid harvesters (Admin only)"""

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
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        return

    # Use utility function for embed building
    fields = {
        "💰 Payroll Summary": f"**Melange Paid:** {total_paid:,} | **Users Paid:** {users_paid} | **Admin:** {interaction.user.display_name}"
    }

    embed = build_status_embed(
        title="💰 Guild Payroll Complete",
        description="**All users with pending melange have been paid!**",
        color=0x27AE60,
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

    logger.info(f'Payroll processed by {interaction.user.display_name} ({interaction.user.id}) - {users_paid} users paid {total_paid:,} melange',
                admin_id=str(interaction.user.id), admin_username=interaction.user.display_name,
                users_paid=users_paid, melange_paid=total_paid)
