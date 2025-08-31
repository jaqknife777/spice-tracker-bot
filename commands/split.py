"""
Split command for dividing harvested spice sand among expedition members.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],
    'description': "Split harvested spice sand among expedition members",
    'params': {
        'total_sand': "Total spice sand collected to split",
        'users': "List of Discord users to split with (use @mentions)"
    }
}

import os
import discord
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, get_sand_per_melange, send_response
from utils.logger import logger


@handle_interaction_expiration
async def split(interaction, total_sand: int, users: str, use_followup: bool = True):
    """Split harvested spice sand among expedition members"""
    try:
        # Validate total_sand input
        if total_sand < 1:
            await send_response(interaction, "❌ Total spice sand must be at least 1.", use_followup=use_followup, ephemeral=True)
            return
        
        # Parse user mentions from the users string
        # Extract user IDs from mentions like <@123456789012345678>
        import re
        user_id_pattern = r'<@!?(\d+)>'
        user_ids = re.findall(user_id_pattern, users)
        
        if not user_ids:
            await send_response(interaction, 
                "❌ Please provide valid Discord user mentions (e.g., @username).\n\n"
                "**Example:** `/split 500 @shon @theycall @ricky`\n"
                "**Note:** Users must be mentioned using @ symbol, not just typed names.", 
                use_followup=use_followup, ephemeral=True)
            return
        
        # Remove duplicates (no automatic initiator inclusion)
        unique_user_ids = list(set(user_ids))
        
        # Validate that we have at least one user to split with
        if not unique_user_ids:
            await send_response(interaction, 
                "❌ You need to mention at least one user to split with.\n\n"
                "**Example:** `/split 500 @username`\n"
                "**Note:** Include @yourself if you want to be part of the split.", 
                use_followup=use_followup, ephemeral=True)
            return
        
        # Get conversion rate
        sand_per_melange = get_sand_per_melange()
        
        # Create expedition record
        expedition_id = await get_database().create_expedition(
            str(interaction.user.id),
            interaction.user.display_name,
            total_sand,
            sand_per_melange=sand_per_melange
        )
        
        if not expedition_id:
            await send_response(interaction, "❌ Failed to create expedition record.", use_followup=use_followup, ephemeral=True)
            return
        
        # Calculate equal share per participant
        total_participants = len(unique_user_ids)
        share_per_participant = total_sand // total_participants
        leftover_sand = total_sand % total_participants
        
        # Process all participants
        participant_details = []
        total_melange = 0
        
        for user_id in unique_user_ids:
            # Get current display name for display purposes only
            display_name = None
            try:
                if interaction.guild:
                    user = await interaction.guild.fetch_member(int(user_id))
                    display_name = user.display_name
                else:
                    # No guild context (DM), try to get user from Discord API
                    try:
                        user = await interaction.client.fetch_user(int(user_id))
                        display_name = user.display_name
                    except:
                        display_name = f"User_{user_id}"
            except Exception as e:
                logger.warning(f"Could not fetch Discord user {user_id}: {e}")
                display_name = f"User_{user_id}"
            
            # Ensure we have a valid display name
            if not display_name or display_name.strip() == "":
                display_name = f"User_{user_id}"
            
            # Calculate participant share (add leftover to first participant)
            participant_sand = share_per_participant
            if leftover_sand > 0 and user_id == unique_user_ids[0]:
                participant_sand += leftover_sand
            
            participant_melange = participant_sand // sand_per_melange
            participant_leftover = participant_sand % sand_per_melange
            
            # Add to database using user_id for all operations
            await get_database().add_expedition_participant(
                expedition_id,
                user_id,  # Use user_id for database operations
                display_name,  # Username only for display
                participant_sand,
                participant_melange,
                participant_leftover,
                is_harvester=False  # All participants are equal in this version
            )
            
            # Create expedition deposit for participant using user_id
            await get_database().add_expedition_deposit(
                user_id,  # Use user_id for database operations
                display_name,  # Username only for display
                participant_sand,
                expedition_id
            )
            
            # Mark if this is the initiator
            initiator_mark = " (initiator)" if user_id == str(interaction.user.id) else ""
            participant_details.append(f"**{display_name}**: {participant_sand:,} sand ({participant_melange:,} melange){initiator_mark}")
            total_melange += participant_melange
        
        # Build response embed
        from utils.embed_builder import EmbedBuilder
        embed = (EmbedBuilder("🏜️ Expedition Created", 
                              description=f"**Expedition #{expedition_id}** has been created and recorded in the database!",
                              color=0xF39C12, timestamp=interaction.created_at)
                 .add_field("📊 Expedition Summary", 
                           f"**Total Sand:** {total_sand:,}\n"
                           f"**Participants:** {total_participants}\n"
                           f"**Equal Share:** {share_per_participant:,} sand per person", inline=False)
                 .add_field("💰 Melange Distribution", 
                           f"**Total Melange:** {total_melange:,}", inline=False)
                 .add_field("📋 Participants", 
                           "\n".join(participant_details), inline=False)
                 .add_field("📋 Database Status", 
                           f"✅ Expedition record created\n"
                           f"✅ Participant shares recorded\n"
                           f"✅ Deposits logged for payout tracking\n"
                           f"🔗 Use `/expedition {expedition_id}` to view details", inline=False)
                 .set_footer(f"Expedition initiated by {interaction.user.display_name}", interaction.user.display_avatar.url))
        
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        
        # Log the expedition creation
        logger.bot_event(f"Expedition {expedition_id} created by {interaction.user.display_name} ({interaction.user.id}) - {total_sand} sand, {total_participants} participants")
        
    except Exception as error:
        logger.error(f"Error in split command: {error}")
        await send_response(interaction, "❌ An error occurred while creating the expedition.", use_followup=use_followup, ephemeral=True)