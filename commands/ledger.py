"""
Ledger command for viewing spice deposit history and melange status.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # ['deposits'] - removed for simplicity
    'description': "View your conversion history and melange status",
    'permission_level': 'user'
}

import time
from utils.database_utils import timed_database_operation, validate_user_exists
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.base_command import command
from utils.helpers import get_database, send_response


@command('ledger')
async def ledger(interaction, command_start, use_followup: bool = True):
    """View your sand conversion history and melange status"""

    # Get user data for melange information
    user = await validate_user_exists(get_database(), str(interaction.user.id), interaction.user.display_name, create_if_missing=False)

    # Get deposit history
    deposits_data, get_deposits_time = await timed_database_operation(
        "get_user_deposits",
        get_database().get_user_deposits,
        str(interaction.user.id)
    )

    if not deposits_data:
        embed = build_status_embed(
            title="📋 Spice Deposit Ledger",
            description="💎 You haven't made any melange yet! Use `/sand` to convert spice sand into melange.",
            color=0x95A5A6,
            timestamp=interaction.created_at
        )
        await send_response(interaction, embed=embed.build(), use_followup=use_followup, ephemeral=True)
        return

    # Build deposit history (sand amounts are just for audit/history)
    ledger_text = ""

    for deposit in deposits_data:
        # Handle null created_at timestamps
        if deposit['created_at'] and hasattr(deposit['created_at'], 'timestamp'):
            date_str = f"<t:{int(deposit['created_at'].timestamp())}:R>"
        else:
            date_str = "Unknown date"

        # Show deposit type and sand amount (for historical record only)
        deposit_type = "🚀 Expedition" if deposit['type'] == 'expedition' else "🏜️ Solo"
        ledger_text += f"**{deposit['sand_amount']:,} sand** {deposit_type} - {date_str}\n"

    # Calculate melange values
    total_melange = user.get('total_melange', 0) if user else 0
    paid_melange = user.get('paid_melange', 0) if user else 0
    pending_melange = total_melange - paid_melange

    fields = {
        "💎 Melange": f"**{total_melange:,}** total | **{paid_melange:,}** paid | **{pending_melange:,}** pending",
        "📊 Activity": f"{len(deposits_data)} conversions"
    }

    embed = build_status_embed(
        title="📋 Conversion History",
        description=ledger_text,
        color=0x3498DB,
        fields=fields,
        thumbnail=interaction.user.display_avatar.url,
        timestamp=interaction.created_at
    )

    # Send response using helper function (ephemeral for privacy)
    response_start = time.time()
    await send_response(interaction, embed=embed.build(), use_followup=use_followup, ephemeral=True)
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
        total_melange=total_melange
    )
