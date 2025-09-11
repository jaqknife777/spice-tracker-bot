"""
Pay command for processing melange payments (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # formerly 'payment'
    'description': "Process melange payment for a user (Admin only)",
    'params': {
        'user': "User to pay",
        'amount': "Amount of melange to pay (optional, defaults to full pending amount)"
    },
    'permission_level': 'admin'
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import get_database, send_response
from utils.base_command import admin_command
from utils.logger import logger


@admin_command('pay')
async def pay(interaction, command_start, user, amount: int = None, use_followup: bool = True):
    """Process melange payment for a user (Admin only)"""

    # Get user's pending melange
    pending_data, get_pending_time = await timed_database_operation(
        "get_user_pending_melange",
        get_database().get_user_pending_melange,
        str(user.id)
    )

    pending_melange = pending_data.get('pending_melange', 0)
    total_melange = pending_data.get('total_melange', 0)
    paid_melange = pending_data.get('paid_melange', 0)

    if pending_melange <= 0:
        embed = build_status_embed(
            title="💰 No Payment Due",
            description=f"**{user.display_name}** has no pending melange.",
            color=0x95A5A6,
            fields={"📊 Status": f"**Total:** {total_melange:,} | **Paid:** {paid_melange:,} | **Pending:** {pending_melange:,}"},
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        return

    # Determine payment amount
    if amount is None:
        # Pay in full
        payment_amount = pending_melange
    else:
        # Validate partial payment amount
        if amount <= 0:
            await send_response(interaction, "❌ Payment amount must be greater than 0.", use_followup=use_followup, ephemeral=True)
            return
        if amount > pending_melange:
            await send_response(interaction, f"❌ Payment amount ({amount:,}) exceeds pending melange ({pending_melange:,}).", use_followup=use_followup, ephemeral=True)
            return
        payment_amount = amount

    # Process the payment
    paid_amount, pay_melange_time = await timed_database_operation(
        "pay_user_melange",
        get_database().pay_user_melange,
        str(user.id), user.display_name, payment_amount,
        str(interaction.user.id), interaction.user.display_name
    )

    # Calculate remaining pending after payment
    remaining_pending = pending_melange - paid_amount

    # Build concise response
    fields = {
        "💰 Payment": f"**{paid_amount:,}** melange | **Admin:** {interaction.user.display_name}",
        "📊 Status": f"**Total:** {total_melange:,} | **Paid:** {paid_melange + paid_amount:,} | **Pending:** {remaining_pending:,}"
    }

    payment_type = "Full payment" if amount is None else "Partial payment"
    embed = build_status_embed(
        title=f"💰 {payment_type} Processed",
        description=f"**{user.display_name}** paid **{paid_amount:,}** melange",
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
        "Melange Payment",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        admin_id=str(interaction.user.id),
        admin_username=interaction.user.display_name,
        target_user_id=str(user.id),
        target_username=user.display_name,
        get_pending_time=f"{get_pending_time:.3f}s",
        pay_melange_time=f"{pay_melange_time:.3f}s",
        response_time=f"{response_time:.3f}s",
        melange_paid=paid_amount,
        total_melange=total_melange
    )

    logger.info(f'User {user.display_name} ({user.id}) paid {paid_amount:,} melange by {interaction.user.display_name} ({interaction.user.id})',
                user_id=str(user.id), username=user.display_name,
                admin_id=str(interaction.user.id), admin_username=interaction.user.display_name,
                melange_paid=paid_amount)
