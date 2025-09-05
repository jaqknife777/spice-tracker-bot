"""
Fixed rate cut command for awarding a percentage of spice sand to users and the rest to the guild.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['frc'],
    'description': "Awards a fixed percentage of spice sand to tagged users, with the remainder going to the guild.",
    'params': {
        'total_sand': "Total spice sand collected to be distributed.",
        'users': "A list of users to award a cut to.",
        'rate': "The percentage rate of the cut for each user (default: 5).",
        'landsraad_bonus': "Whether or not to apply the 25% Landsraad crafting reduction (default: false)."
    }
}

import re
import traceback
import discord
import math
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, get_sand_per_melange, send_response
from utils.logger import logger

@handle_interaction_expiration
async def fixedratecut(interaction, total_sand: int, users: str, rate: int = 5, landsraad_bonus: bool = False, use_followup: bool = True):
    """Awards a fixed percentage of spice sand to tagged users, with the remainder going to the guild."""
    try:
        # Validate inputs
        if total_sand < 1:
            await send_response(interaction, "❌ Total spice sand must be at least 1.", use_followup=use_followup, ephemeral=True)
            return

        if not 0 <= rate <= 100:
            await send_response(interaction, "❌ Rate must be between 0 and 100.", use_followup=use_followup, ephemeral=True)
            return

        # Parse users string for mentions
        pattern = r'<@!?(\d+)>'
        user_ids = re.findall(pattern, users)

        if not user_ids:
            await send_response(interaction,
                "❌ Please provide valid Discord user mentions.\n\n"
                "**Example:**\n"
                "• `/fixedratecut total_sand:10000 users:\"@user1 @user2\" rate:10`",
                use_followup=use_followup, ephemeral=True)
            return

        # Remove duplicate user_ids
        user_ids = list(set(user_ids))
        num_users = len(user_ids)

        if num_users * rate > 100:
            await send_response(interaction, f"❌ The total cut for all users ({num_users} * {rate}% = {num_users * rate}%) cannot exceed 100%.", use_followup=use_followup, ephemeral=True)
            return

        # Calculations
        user_sand = int(total_sand * (rate / 100))
        total_user_sand = user_sand * num_users
        guild_sand = total_sand - total_user_sand

        # Get conversion rate
        sand_per_melange = get_sand_per_melange(landsraad_bonus=landsraad_bonus)

        # Ensure the initiator exists in the users table
        from utils.database_utils import validate_user_exists
        await validate_user_exists(get_database(), str(interaction.user.id), interaction.user.display_name)

        # Create expedition record
        expedition_id = await get_database().create_expedition(
            str(interaction.user.id),
            interaction.user.display_name,
            total_sand,
            sand_per_melange=sand_per_melange,
            guild_cut_percentage=(guild_sand / total_sand * 100) if total_sand > 0 else 0
        )

        if not expedition_id:
            await send_response(interaction, "❌ Failed to create expedition record.", use_followup=use_followup, ephemeral=True)
            return

        # Add guild cut to treasury if > 0
        if guild_sand > 0:
            guild_melange = math.ceil(guild_sand / sand_per_melange) if sand_per_melange > 0 else 0
            await get_database().update_guild_treasury(guild_sand, guild_melange)

        # Process all participants
        participant_details = []
        total_user_melange = 0

        for user_id in user_ids:
            try:
                # Try to get user from guild first, then client
                try:
                    user = await interaction.guild.fetch_member(int(user_id))
                    display_name = user.display_name
                except (discord.NotFound, discord.HTTPException):
                    try:
                        user = await interaction.client.fetch_user(int(user_id))
                        display_name = user.display_name
                    except (discord.NotFound, discord.HTTPException):
                        display_name = f"User_{user_id}"

                # Ensure user exists in database
                await validate_user_exists(get_database(), user_id, display_name)

                # Calculate melange
                participant_melange = math.ceil(user_sand / sand_per_melange) if sand_per_melange > 0 else 0
                total_user_melange += participant_melange

                # Add expedition participant
                await get_database().add_expedition_participant(
                    expedition_id, user_id, display_name, user_sand,
                    participant_melange, is_harvester=False
                )

                # Add deposit record
                await get_database().add_deposit(user_id, display_name, user_sand, expedition_id=expedition_id)

                # Update user's melange total if they earned melange
                if participant_melange > 0:
                    await get_database().update_user_melange(user_id, participant_melange)

                # Format for display
                participant_details.append(f"**{display_name}**: {user_sand:,} sand ({participant_melange:,} melange)")

            except Exception as participant_error:
                logger.error(f"Error processing participant {user_id}: {participant_error}")
                participant_details.append(f"**User_{user_id}**: {user_sand:,} sand (error processing)")

        # Build response embed
        from utils.embed_utils import build_status_embed

        guild_cut_percentage = (guild_sand / total_sand * 100) if total_sand > 0 else 0
        guild_melange_total = math.ceil(guild_sand / sand_per_melange) if sand_per_melange > 0 else 0

        fields = {
            "👥 Participants": "\n".join(participant_details),
            "🏛️ Guild Cut": f"**{guild_cut_percentage:.1f}%** = {guild_sand:,} sand → **{guild_melange_total:,} melange**",
            "📊 Summary": f"**Total:** {total_sand:,} | **Users:** {total_user_sand:,} sand → **{total_user_melange:,} melange**"
        }

        embed = build_status_embed(
            title="💸 Fixed Rate Cut Completed",
            description=f"**Expedition #{expedition_id}** - {num_users} participants at a {rate}% rate.",
            color=0x00FF00,
            fields=fields,
            timestamp=interaction.created_at
        )

        # Send response
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)

        # Log the expedition creation
        logger.info(f"Fixed Rate Cut {expedition_id} created by {interaction.user.display_name} ({interaction.user.id})",
                   total_sand=total_sand, guild_sand=guild_sand, participants=num_users, rate=rate)

    except Exception as error:
        logger.error(f"Error in fixedratecut command: {error}")
        logger.error(f"Fixedratecut command traceback: {traceback.format_exc()}")

        try:
            await send_response(interaction, "❌ An error occurred while processing the fixed rate cut. Please try again.", use_followup=use_followup, ephemeral=True)
        except Exception as response_error:
            logger.error(f"Failed to send error response: {response_error}")
