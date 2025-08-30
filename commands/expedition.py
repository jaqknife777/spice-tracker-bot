"""
Expedition command for viewing details of a specific expedition.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['exp'],
    'description': "View details of a specific expedition",
    'params': {'expedition_id': "ID of the expedition to view"}
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, send_response
from utils.logger import logger


@handle_interaction_expiration
async def expedition_details(interaction, expedition_id: int, use_followup: bool = True):
    """View details of a specific expedition"""
    command_start = time.time()
    
    try:
        # Get expedition details using utility function
        expedition_participants, get_participants_time = await timed_database_operation(
            "get_expedition_participants",
            get_database().get_expedition_participants,
            expedition_id
        )
        
        if not expedition_participants:
            await send_response(interaction, "❌ Expedition not found or you don't have access to it.", use_followup=use_followup, ephemeral=True)
            return
        
        # Build participant list
        participant_details = []
        total_sand = 0
        
        for participant in expedition_participants:
            role = "🏭 Primary Harvester" if participant['is_harvester'] else "👥 Expedition Member"
            status = "✅ Paid" if participant['sand_amount'] == 0 else "⏳ Unpaid"
            participant_details.append(f"{role}: **{participant['username']}**\n"
                                    f"   Sand: {participant['sand_amount']:,} | Melange: {participant['melange_amount']:,} | Leftover: {participant['leftover_sand']:,} - {status}")
            total_sand += participant['sand_amount']
        
        # Use utility function for embed building
        fields = {
            "📋 Expedition Participants": "\n\n".join(participant_details)
        }
        
        embed = build_status_embed(
            title=f"🏜️ Expedition #{expedition_id}",
            description=f"**Total Sand Distributed:** {total_sand:,}\n**Participants:** {len(expedition_participants)}",
            color=0xF39C12,
            fields=fields,
            footer=f"Requested by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        
        # Send response using helper function
        response_start = time.time()
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        response_time = time.time() - response_start
        
        # Log performance metrics using utility function
        total_time = time.time() - command_start
        log_command_metrics(
            "Expedition Details",
            str(interaction.user.id),
            interaction.user.display_name,
            total_time,
            expedition_id=expedition_id,
            get_participants_time=f"{get_participants_time:.3f}s",
            response_time=f"{response_time:.3f}s",
            participant_count=len(expedition_participants),
            total_sand=total_sand
        )
        
    except Exception as error:
        total_time = time.time() - command_start
        logger.error(f"Error in expedition_details command: {error}", 
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    expedition_id=expedition_id,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, "❌ An error occurred while fetching expedition details.", use_followup=use_followup, ephemeral=True)
