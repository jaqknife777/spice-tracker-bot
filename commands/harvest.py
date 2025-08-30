"""
Harvest command for logging spice sand harvests and calculating melange conversion.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['sand'],
    'description': "Log spice sand harvests and calculate melange conversion",
    'params': {'amount': "Amount of spice sand harvested"}
}

import time
from utils.database_utils import timed_database_operation, validate_user_exists, get_user_stats
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, get_sand_per_melange, send_response


@handle_interaction_expiration
async def harvest(interaction, amount: int, use_followup: bool):
    """Log spice sand harvests and calculate melange conversion"""
    command_start = time.time()
    
    # Validate amount
    if not 1 <= amount <= 10000:
        await send_response(interaction, "❌ Amount must be between 1 and 10,000 spice sand.", use_followup=use_followup, ephemeral=True)
        return
    
    # Get conversion rate and add deposit
    sand_per_melange = get_sand_per_melange()
    
    # Database operations with timing using utility functions
    
    # Add deposit with timing
    add_deposit_time = await timed_database_operation(
        "add_deposit",
        get_database().add_deposit,
        str(interaction.user.id), interaction.user.display_name, amount
    )
    
    # Get user data and calculate totals
    user_stats = await get_user_stats(get_database(), str(interaction.user.id))
    
    # Ensure user exists and has valid data
    user = await validate_user_exists(get_database(), str(interaction.user.id), interaction.user.display_name)
    
    # Calculate melange conversion
    total_melange_earned = user_stats['total_sand'] // sand_per_melange
    current_melange = user['total_melange'] if user and user['total_melange'] is not None else 0
    new_melange = max(0, total_melange_earned - current_melange)  # Ensure new_melange is never negative
    
    # Only update melange if we have new melange to add
    if new_melange > 0:
        update_melange_time = await timed_database_operation(
            "update_user_melange",
            get_database().update_user_melange,
            str(interaction.user.id), new_melange
        )
    
    # Build response
    remaining_sand = user_stats['total_sand'] % sand_per_melange
    sand_needed = max(0, sand_per_melange - remaining_sand)  # Ensure sand_needed is never negative
    
    # Use utility function for embed building
    fields = {
        "📊 Harvest Summary": f"**Spice Sand Harvested:** {amount:,}\n**Total Unpaid Harvest:** {user_stats['total_sand']:,}",
        "✨ Melange Production": f"**Total Melange:** {(current_melange + new_melange):,}\n**Conversion Rate:** {sand_per_melange} sand = 1 melange",
        "🎯 Next Refinement": f"**Sand Until Next Melange:** {sand_needed:,}"
    }
    
    embed = build_status_embed(
        title="🏜️ Spice Harvest Logged",
        color=0xE67E22,
        fields=fields,
        footer=f"Harvested by {interaction.user.display_name}",
        timestamp=interaction.created_at
    )
    
    if new_melange and new_melange > 0:
        embed.set_description(f"🎉 **You produced {new_melange:,} melange from this harvest!**")
    
    # Send response using helper function
    response_start = time.time()
    await send_response(interaction, embed=embed.build(), use_followup=use_followup)
    response_time = time.time() - response_start
    
    # Log performance metrics using utility function
    total_time = time.time() - command_start
    log_command_metrics(
        "Harvest",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        amount=amount,
        add_deposit_time=f"{add_deposit_time:.3f}s",
        **user_stats['timing'],
        response_time=f"{response_time:.3f}s",
        new_melange=new_melange
    )
