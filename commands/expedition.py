"""
Expedition command for viewing details of a specific expedition.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # ['exp'] - removed for simplicity
    'description': "View details of a specific expedition",
    'params': {'expedition_id': "ID of the expedition to view"},
    'permission_level': 'user'
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.base_command import command
from utils.helpers import get_database, send_response
from utils.logger import logger


@command('expedition')
async def expedition(interaction, command_start, expedition_id: int, use_followup: bool = True):
    """View details of a specific expedition"""

    try:
        # Get expedition details using utility function
        expedition_data, get_participants_time = await timed_database_operation(
            "get_expedition_participants",
            get_database().get_expedition_participants,
            expedition_id
        )

        if not expedition_data:
            await send_response(interaction, "❌ Expedition not found or you don't have access to it.", use_followup=use_followup, ephemeral=True)
            return

        expedition = expedition_data['expedition']
        expedition_participants = expedition_data['participants']

        # Calculate guild cut amounts
        guild_cut_percentage = expedition['guild_cut_percentage']
        total_expedition_sand = expedition['total_sand']
        guild_sand = int(total_expedition_sand * (guild_cut_percentage / 100))
        user_sand = total_expedition_sand - guild_sand

        # Build participant list
        participant_details = []
        total_participant_sand = 0

        for participant in expedition_participants:
            role = "🏭 Primary Harvester" if participant['is_harvester'] else "👥 Expedition Member"
            # Note: Expedition participants show sand allocation, not payment status (payments are user-level)
            participant_details.append(f"{role}: **{participant['username']}**\n"
                                    f"   Sand: {participant['sand_amount']:,} | Melange: {participant['melange_amount']:,} | Leftover: {participant['leftover_sand']:,}")
            total_participant_sand += participant['sand_amount']

        # Use utility function for embed building
        fields = {
            "🏛️ Guild Cut": f"**Guild Cut:** {guild_cut_percentage}% ({guild_sand:,} sand)\n**Guild Melange:** {guild_sand // expedition['sand_per_melange']:,}",
            "📋 Expedition Participants": "\n\n".join(participant_details) if participant_details else "No participants",
            "📊 Expedition Summary": f"**Initiator:** {expedition['initiator_username']}\n**Total Sand:** {total_expedition_sand:,}\n**User Sand:** {user_sand:,}\n**Participants:** {len(expedition_participants)}"
        }

        embed = build_status_embed(
            title=f"🏜️ Expedition #{expedition_id}",
            description=f"⚗️ **Sand per Melange:** {expedition['sand_per_melange']} | 🗓️ **Created:** {expedition['created_at'].strftime('%Y-%m-%d %H:%M UTC')}",
            color=0xF39C12,
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
            "Expedition Details",
            str(interaction.user.id),
            interaction.user.display_name,
            total_time,
            expedition_id=expedition_id,
            get_participants_time=f"{get_participants_time:.3f}s",
            response_time=f"{response_time:.3f}s",
            participant_count=len(expedition_participants),
            total_expedition_sand=total_expedition_sand,
            guild_cut_percentage=guild_cut_percentage,
            guild_sand=guild_sand
        )

    except Exception as error:
        total_time = time.time() - command_start
        logger.error(f"Error in expedition command: {error}",
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    expedition_id=expedition_id,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, "❌ An error occurred while fetching expedition details.", use_followup=use_followup, ephemeral=True)
