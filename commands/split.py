"""
Split command for dividing harvested spice sand among expedition members with guild cut and individual percentages.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],
    'description': "Split harvested spice sand among expedition members with guild cut and individual percentages",
    'params': {
        'total_sand': "Total spice sand collected to split",
        'users': "Users and percentages: '@user1 50 @user2 @user3' (users without % split equally)",
        'guild': "Guild cut percentage (default: 10)"
    }
}

import re
import traceback
import discord
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, get_sand_per_melange, send_response
from utils.logger import logger


@handle_interaction_expiration
async def split(interaction, total_sand: int, users: str, guild: int = 10, use_followup: bool = True):
    """Split harvested spice sand among expedition members with guild cut and individual percentages"""
    
    try:
        # Validate inputs
        if total_sand < 1:
            await send_response(interaction, "❌ Total spice sand must be at least 1.", use_followup=use_followup, ephemeral=True)
            return
        
        if not 0 <= guild <= 100:
            await send_response(interaction, "❌ Guild cut percentage must be between 0 and 100.", use_followup=use_followup, ephemeral=True)
            return
        
        # Parse users string for mentions and percentages
        # Format: "@user1 50 @user2 @user3 25" etc.
        user_data = []
        percentage_users = []
        equal_split_users = []
        
        # Extract user mentions and optional percentages
        # Pattern: @user_id optionally followed by a number
        pattern = r'<@!?(\d+)>\s*(\d+)?'
        matches = re.findall(pattern, users)
        
        if not matches:
            await send_response(interaction, 
                "❌ Please provide valid Discord user mentions.\n\n"
                "**Examples:**\n"
                "• Equal split: `/split total_sand:1000 users:\"@user1 @user2\"`\n"
                "• Percentage split: `/split total_sand:1000 users:\"@leader 60 @member1 @member2\"`\n"
                "• Mixed: `/split total_sand:1000 users:\"@leader 40 @member1 @member2\" guild:5`", 
                use_followup=use_followup, ephemeral=True)
            return
        
        total_percentage = 0
        for user_id, percentage_str in matches:
            if percentage_str:  # User has a percentage
                percentage = int(percentage_str)
                if not 0 <= percentage <= 100:
                    await send_response(interaction, f"❌ Percentage {percentage} is invalid. Must be between 0-100.", use_followup=use_followup, ephemeral=True)
                    return
                percentage_users.append((user_id, percentage))
                total_percentage += percentage
            else:  # User will get equal split
                equal_split_users.append(user_id)
        
        # Validate percentages don't exceed 100%
        if total_percentage > 100:
            await send_response(interaction, f"❌ Total user percentages ({total_percentage}%) cannot exceed 100%.", use_followup=use_followup, ephemeral=True)
            return
        
        # Calculate guild cut first
        guild_sand = int(total_sand * (guild / 100))
        remaining_sand = total_sand - guild_sand
        
        # Calculate user distributions
        user_distributions = []
        remaining_after_percentages = remaining_sand
        
        # First, allocate to percentage users
        for user_id, percentage in percentage_users:
            user_sand = int(remaining_sand * (percentage / 100))
            user_distributions.append((user_id, user_sand, percentage))
            remaining_after_percentages -= user_sand
        
        # Then, split remaining sand equally among non-percentage users
        if equal_split_users:
            equal_share = remaining_after_percentages // len(equal_split_users)
            leftover = remaining_after_percentages % len(equal_split_users)
            
            for i, user_id in enumerate(equal_split_users):
                # Give leftover sand to first few users
                user_sand = equal_share + (1 if i < leftover else 0)
                equal_percentage = (user_sand / remaining_sand) * 100 if remaining_sand > 0 else 0
                user_distributions.append((user_id, user_sand, equal_percentage))
        
        # Remove duplicates and validate we have users
        unique_distributions = {}
        for user_id, sand, percentage in user_distributions:
            if user_id in unique_distributions:
                # Combine if user mentioned multiple times
                existing_sand, existing_pct = unique_distributions[user_id]
                unique_distributions[user_id] = (existing_sand + sand, existing_pct + percentage)
            else:
                unique_distributions[user_id] = (sand, percentage)
        
        if not unique_distributions:
            await send_response(interaction, "❌ No valid users found to split with.", use_followup=use_followup, ephemeral=True)
            return
        
        # Get conversion rate
        sand_per_melange = get_sand_per_melange()
        
        # Ensure the initiator exists in the users table
        from utils.database_utils import validate_user_exists
        await validate_user_exists(get_database(), str(interaction.user.id), interaction.user.display_name)
        
        # Create expedition record with guild cut
        expedition_id = await get_database().create_expedition(
            str(interaction.user.id),
            interaction.user.display_name,
            total_sand,
            sand_per_melange=sand_per_melange,
            guild_cut_percentage=guild
        )
        
        if not expedition_id:
            await send_response(interaction, "❌ Failed to create expedition record.", use_followup=use_followup, ephemeral=True)
            return
        
        # Add guild cut to treasury if > 0
        if guild_sand > 0:
            guild_melange = guild_sand // sand_per_melange
            await get_database().update_guild_treasury(guild_sand, guild_melange)
        
        # Process all participants
        participant_details = []
        total_user_melange = 0
        
        for user_id, (user_sand, user_percentage) in unique_distributions.items():
            try:
                # Try to get user from guild first, then client
                try:
                    user = await interaction.guild.fetch_member(int(user_id))
                    display_name = user.display_name
                except:
                    try:
                        user = await interaction.client.fetch_user(int(user_id))
                        display_name = user.display_name
                    except:
                        display_name = f"User_{user_id}"
                
                # Ensure user exists in database
                await validate_user_exists(get_database(), user_id, display_name)
                
                # Calculate melange and leftover sand
                participant_melange = user_sand // sand_per_melange
                participant_leftover = user_sand % sand_per_melange
                total_user_melange += participant_melange
                
                # Add expedition participant
                await get_database().add_expedition_participant(
                    expedition_id, user_id, display_name, user_sand, 
                    participant_melange, participant_leftover, is_harvester=False
                )
                
                # Add deposit record
                await get_database().add_deposit(user_id, display_name, user_sand, expedition_id=expedition_id)
                
                # Format for display
                percentage_text = f" ({user_percentage:.1f}%)" if user_percentage > 0 else ""
                participant_details.append(f"**{display_name}**: {user_sand:,} sand ({participant_melange:,} melange){percentage_text}")
                
            except Exception as participant_error:
                logger.error(f"Error processing participant {user_id}: {participant_error}")
                participant_details.append(f"**User_{user_id}**: {user_sand:,} sand (error processing)")
        
        # Build response embed
        from utils.embed_utils import build_status_embed
        
        fields = {
            "🏛️ Guild Treasury": f"**Guild Cut:** {guild}% ({guild_sand:,} sand)\n**Guild Melange:** {guild_sand // sand_per_melange:,}",
            "👥 Expedition Participants": "\n".join(participant_details),
            "📊 Split Summary": f"**Total Sand:** {total_sand:,}\n"
                               f"**Guild Cut:** {guild_sand:,} sand ({guild}%)\n"
                               f"**User Sand:** {remaining_sand:,} sand\n"
                               f"**Total User Melange:** {total_user_melange:,}",
        }
        
        embed = build_status_embed(
            title="🏜️ Expedition Split Completed",
            description=f"**Expedition #{expedition_id}** - {len(unique_distributions)} participants",
            color=0x00FF00,
            fields=fields,
            footer=f"Initiated by {interaction.user.display_name}",
            timestamp=interaction.created_at
        )
        
        # Send response
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        
        # Log the expedition creation
        logger.info(f"Expedition {expedition_id} created by {interaction.user.display_name} ({interaction.user.id})", 
                   total_sand=total_sand, guild_cut=guild_sand, participants=len(unique_distributions))
        
    except Exception as error:
        logger.error(f"Error in split command: {error}")
        logger.error(f"Split command traceback: {traceback.format_exc()}")
        
        try:
            await send_response(interaction, "❌ An error occurred while processing the split. Please try again.", use_followup=use_followup, ephemeral=True)
        except Exception as response_error:
            logger.error(f"Failed to send error response: {response_error}")