"""
Payment command for processing payment for a harvester's deposits (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['pay'],
    'description': "Process payment for a harvester's deposits (Admin only)",
    'params': {'user': "Harvester to pay"}
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, send_response
from utils.permissions import is_admin


@handle_interaction_expiration
async def payment(interaction, user, use_followup: bool = True):
    """Process payment for a harvester's deposits (Admin only)"""
    command_start = time.time()
    
    # Check if user has admin permissions
    if not is_admin(interaction):
        await send_response(interaction, "❌ You need an admin role to use this command. Contact a server administrator.", use_followup=use_followup, ephemeral=True)
        return
    
    # Get user's unpaid deposits using utility function
    unpaid_deposits, get_deposits_time = await timed_database_operation(
        "get_user_deposits",
        get_database().get_user_deposits,
        str(user.id), False
    )
    
    if not unpaid_deposits:
        embed = build_status_embed(
            title="💰 Payment Status",
            description=f"🏜️ **{user.display_name}** has no unpaid harvests to process.",
            color=0x95A5A6,
            footer=f"Requested by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        return
    
    # Mark all deposits as paid using utility function
    _, update_time = await timed_database_operation(
        "mark_all_user_deposits_paid",
        get_database().mark_all_user_deposits_paid,
        str(user.id)
    )
    
    total_paid = sum(deposit['sand_amount'] for deposit in unpaid_deposits)
    
    # Use utility function for embed building
    fields = {
        "📊 Payment Summary": f"**Total Spice Sand Paid:** {total_paid:,}\n**Harvests Processed:** {len(unpaid_deposits)}"
    }
    
    embed = build_status_embed(
        title="💰 Payment Processed",
        description=f"**{user.display_name}** has been paid for all harvests!",
        color=0x27AE60,
        fields=fields,
        footer=f"Payment processed by {interaction.user.display_name}",
        timestamp=interaction.created_at
    )
    
    # Send response using helper function
    response_start = time.time()
    await send_response(interaction, embed=embed.build(), use_followup=use_followup)
    response_time = time.time() - response_start
    
    # Log performance metrics using utility function
    total_time = time.time() - command_start
    log_command_metrics(
        "Payment",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        admin_id=str(interaction.user.id),
        admin_username=interaction.user.display_name,
        target_user_id=str(user.id),
        target_username=user.display_name,
        get_deposits_time=f"{get_deposits_time:.3f}s",
        update_time=f"{update_time:.3f}s",
        response_time=f"{response_time:.3f}s",
        total_paid=total_paid,
        harvests_processed=len(unpaid_deposits)
    )
    
    print(f'Harvester {user.display_name} ({user.id}) paid {total_paid:,} spice sand by {interaction.user.display_name} ({interaction.user.id})')
