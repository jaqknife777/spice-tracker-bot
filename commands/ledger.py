"""
Ledger command for viewing complete spice harvest ledger.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['deposits'],
    'description': "View your complete spice harvest ledger"
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, send_response


@handle_interaction_expiration
async def ledger(interaction, use_followup: bool = True):
    """View your complete spice harvest ledger"""
    command_start = time.time()
    
    # Database operation with timing using utility function
    deposits_data, get_deposits_time = await timed_database_operation(
        "get_user_deposits",
        get_database().get_user_deposits,
        str(interaction.user.id)
    )
    
    if not deposits_data:
        embed = build_status_embed(
            title="📋 Spice Harvest Ledger",
            description="🏜️ You haven't harvested any spice sand yet! Use `/harvest` to start tracking your harvests.",
            color=0x95A5A6,
            footer=f"Requested by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup, ephemeral=True)
        return
    
    # Build harvest ledger
    ledger_text = ""
    total_unpaid = 0
    total_paid = 0
    
    for deposit in deposits_data:
        status = "✅ Paid" if deposit['paid'] else "⏳ Unpaid"
        date_str = f"<t:{int(deposit['created_at'].timestamp())}:R>"
        ledger_text += f"**{deposit['sand_amount']:,} spice sand** - {status} - {date_str}\n"
        
        if deposit['paid']:
            total_paid += deposit['sand_amount']
        else:
            total_unpaid += deposit['sand_amount']
    
    # Use utility function for embed building
    fields = {
        "💰 Payment Summary": f"**Unpaid Harvest:** {total_unpaid:,} sand\n**Paid Harvest:** {total_paid:,} sand\n**Total Harvests:** {len(deposits_data)}"
    }
    
    embed = build_status_embed(
        title="📋 Spice Harvest Ledger",
        description=ledger_text,
        color=0x3498DB,
        fields=fields,
        footer=f"Spice Refinery • {interaction.user.display_name}",
        thumbnail=interaction.user.display_avatar.url,
        timestamp=interaction.created_at
    )
    
    # Send response using helper function
    response_start = time.time()
    await send_response(interaction, embed=embed.build(), use_followup=use_followup)
    response_time = time.time() - response_start
    
    # Log performance metrics using utility function
    total_time = time.time() - command_start
    log_command_metrics(
        "Ledger",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        get_deposits_time=f"{get_deposits_time:.3f}s",
        response_time=f"{response_time:.3f}s",
        result_count=len(deposits_data),
        total_unpaid=total_unpaid,
        total_paid=total_paid
    )
