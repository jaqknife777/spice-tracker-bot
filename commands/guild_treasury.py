"""
Guild Treasury command for viewing guild's accumulated resources.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['treasury', 'guild'],
    'description': "View guild treasury balance and statistics",
    'params': {}
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, get_sand_per_melange, send_response


@handle_interaction_expiration
async def guild_treasury(interaction, use_followup: bool = True):
    """View guild treasury balance and statistics"""
    command_start = time.time()
    
    try:
        # Get guild treasury data
        treasury_data, get_treasury_time = await timed_database_operation(
            "get_guild_treasury",
            get_database().get_guild_treasury
        )
        
        sand_per_melange = get_sand_per_melange()
        
        # Calculate additional stats
        total_sand = treasury_data.get('total_sand', 0)
        total_melange = treasury_data.get('total_melange', 0)
        melange_potential = total_sand // sand_per_melange
        sand_ready_for_melange = total_sand - (total_sand % sand_per_melange)
        sand_remaining = total_sand % sand_per_melange
        
        # Format timestamps
        created_at = treasury_data.get('created_at')
        last_updated = treasury_data.get('last_updated')
        
        created_str = created_at.strftime('%Y-%m-%d %H:%M UTC') if created_at else 'Unknown'
        updated_str = last_updated.strftime('%Y-%m-%d %H:%M UTC') if last_updated else 'Never'
        
        # Build response embed
        fields = {
            "🏛️ Treasury Balance": f"**Total Sand:** {total_sand:,}\n**Total Melange:** {total_melange:,}",
            "⚗️ Conversion Potential": f"**Sand Ready for Melange:** {sand_ready_for_melange:,}\n**Potential Melange:** {melange_potential:,}\n**Remaining Sand:** {sand_remaining:,}",
            "📊 Treasury Info": f"**Created:** {created_str}\n**Last Updated:** {updated_str}\n**Conversion Rate:** {sand_per_melange} sand = 1 melange"
        }
        
        # Determine color based on treasury size
        if total_sand >= 10000:
            color = 0xFFD700  # Gold - very wealthy
        elif total_sand >= 5000:
            color = 0x00FF00  # Green - healthy
        elif total_sand >= 1000:
            color = 0xFFA500  # Orange - moderate
        else:
            color = 0xFF4500  # Red - low funds
        
        embed = build_status_embed(
            title="🏛️ Guild Treasury",
            description=f"💰 **Total Value:** {total_sand:,} sand + {total_melange:,} melange",
            color=color,
            fields=fields,
            footer=f"Requested by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        
        # Send response
        response_start = time.time()
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        response_time = time.time() - response_start
        
        # Log metrics
        total_time = time.time() - command_start
        log_command_metrics(
            "Guild Treasury",
            str(interaction.user.id),
            interaction.user.display_name,
            total_time,
            get_treasury_time=f"{get_treasury_time:.3f}s",
            response_time=f"{response_time:.3f}s",
            total_sand=total_sand,
            total_melange=total_melange,
            melange_potential=melange_potential
        )
        
    except Exception as error:
        total_time = time.time() - command_start
        from utils.logger import logger
        logger.error(f"Error in guild_treasury command: {error}", 
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, "❌ An error occurred while fetching guild treasury data.", use_followup=use_followup, ephemeral=True)
