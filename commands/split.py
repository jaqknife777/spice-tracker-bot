"""
Split command for dividing harvested spice sand among expedition members with guild cut and individual percentages.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],
    'description': "Split spice sand among expedition members and convert to melange with guild cut.",
    'params': {
        'total_sand': "Total spice sand collected to split.",
        'users': "Users to include in the split (e.g., '@user1 @user2').",
        'guild': "Guild cut percentage (default: 10).",
        'user_cut': "Optional: Assign a uniform percentage to all users (e.g., 20 for 20%)."
    },
    'permission_level': 'user'
}

import re
import traceback
import discord
from typing import Optional
from utils.base_command import command
from utils.helpers import get_database, convert_sand_to_melange, send_response, get_sand_per_melange_with_bonus, get_guild_cut, get_user_cut
from utils.logger import logger


@command('split')
async def split(interaction, command_start, total_sand: int, users: str, guild: Optional[int] = None, user_cut: Optional[int] = None, use_followup: bool = True):
    """Split spice sand among expedition members and convert to melange with guild cut"""

    # Determine effective cuts, giving priority to command options over global settings
    if guild is None:
        guild = get_guild_cut()

    if user_cut is None:
        user_cut = get_user_cut()

    try:
        # Validate inputs
        if total_sand < 1:
            await send_response(interaction, "❌ Total spice sand must be at least 1.", use_followup=use_followup, ephemeral=True)
            return

        if not 0 <= guild <= 100:
            await send_response(interaction, "❌ Guild cut percentage must be between 0 and 100.", use_followup=use_followup, ephemeral=True)
            return

        # Validate user_cut if provided
        if user_cut is not None and not 0 <= user_cut <= 100:
            await send_response(interaction, "❌ User cut percentage must be between 0 and 100.", use_followup=use_followup, ephemeral=True)
            return

        # Parse users string for mentions and percentages
        percentage_users = []
        equal_split_users = []
        pattern = r'<@!?(\d+)>\s*(\d+)?'
        matches = re.findall(pattern, users)

        if not matches:
            await send_response(interaction,
                "❌ Please provide valid Discord user mentions.\n\n"
                "**Examples:**\n"
                "• Equal split: `/split total_sand:1000 users:\"@user1 @user2\"`\n"
                "• Percentage split: `/split total_sand:1000 users:\"@leader 60 @member1 @member2\"`\n"
                "• Uniform cut: `/split total_sand:1000 users:\"@user1 @user2\" user_cut:20`",
                use_followup=use_followup, ephemeral=True)
            return

        # Process users and calculate total percentage
        total_percentage = 0
        if user_cut is not None:
            if any(percentage_str for _, percentage_str in matches):
                await send_response(interaction, "❌ You cannot provide individual percentages when using `user_cut`.", use_followup=use_followup, ephemeral=True)
                return
            percentage_users = [(user_id, user_cut) for user_id, _ in matches]
            total_percentage = len(matches) * user_cut
        else:
            for user_id, percentage_str in matches:
                if percentage_str:
                    percentage = int(percentage_str)
                    if not 0 <= percentage <= 100:
                        await send_response(interaction, f"❌ Percentage {percentage} is invalid. Must be between 0-100.", use_followup=use_followup, ephemeral=True)
                        return
                    percentage_users.append((user_id, percentage))
                    total_percentage += percentage
                else:
                    equal_split_users.append(user_id)

        # Validate and adjust percentages
        if total_percentage > 100:
            await send_response(interaction, f"❌ Total user percentages ({total_percentage}%) cannot exceed 100%.", use_followup=use_followup, ephemeral=True)
            return

        is_all_percentage = percentage_users and not equal_split_users

        # If percentages are specified, they determine the guild cut. Warn if it differs from the input 'guild' value.
        if is_all_percentage:
            if total_percentage + guild != 100:
                warning_message = f"⚠️ Note: User percentages ({total_percentage}%) and the specified guild cut ({guild}%) do not sum to 100%. The guild cut will be adjusted to be the remainder."
                await send_response(interaction, warning_message, use_followup=use_followup, ephemeral=True)
        elif percentage_users and total_percentage + guild > 100:
            original_guild_cut = guild
            guild = 100 - total_percentage
            warning_message = f"⚠️ Note: User percentages ({total_percentage}%) and the specified guild cut ({original_guild_cut}%) do not sum to 100%. The guild cut will be adjusted to be the remainder."
            await send_response(interaction, warning_message, use_followup=use_followup, ephemeral=True)

        # Convert total sand to melange
        total_melange, remaining_sand = await convert_sand_to_melange(total_sand)
        conversion_rate = await get_sand_per_melange_with_bonus()

        # Calculate user melange distributions
        user_distributions = []
        if is_all_percentage:
            # --- All Percentage Mode ---
            for user_id, percentage in percentage_users:
                user_melange = int(total_melange * (percentage / 100))
                user_distributions.append((user_id, user_melange, percentage))
        else:
            # --- Equal or Mixed Mode ---
            guild_melange_cut = int(total_melange * (guild / 100))
            melange_for_players = total_melange - guild_melange_cut
            melange_given_to_percentage_users = 0
            for user_id, percentage in percentage_users:
                user_melange = int(total_melange * (percentage / 100))
                user_distributions.append((user_id, user_melange, percentage))
                melange_given_to_percentage_users += user_melange

            melange_for_equal_split = melange_for_players - melange_given_to_percentage_users
            if equal_split_users:
                equal_share = melange_for_equal_split // len(equal_split_users)
                for user_id in equal_split_users:
                    user_melange = equal_share
                    equal_percentage = (user_melange / total_melange) * 100 if total_melange > 0 else 0
                    user_distributions.append((user_id, user_melange, equal_percentage))

        # Remove duplicates and validate we have users
        unique_distributions = {}
        for user_id, melange, percentage in user_distributions:
            if user_id in unique_distributions:
                # Combine if user mentioned multiple times
                existing_melange, existing_pct = unique_distributions[user_id]
                unique_distributions[user_id] = (existing_melange + melange, existing_pct + percentage)
            else:
                unique_distributions[user_id] = (melange, percentage)

        if not unique_distributions:
            await send_response(interaction, "❌ No valid users found to split with.", use_followup=use_followup, ephemeral=True)
            return

        # Calculate remaining melange that goes to guild
        total_user_melange = sum(melange for melange, _ in unique_distributions.values())
        guild_melange = total_melange - total_user_melange

        guild_sand = remaining_sand  # Any leftover sand also goes to guild

        # For display purposes, calculate the sand equivalent of the melange
        display_guild_sand = int(guild_melange * conversion_rate) + guild_sand

        # Calculate the total sand value of the guild's cut for percentage calculation
        total_guild_sand_value = (guild_melange * conversion_rate) + guild_sand


        # Ensure the initiator exists in the users table
        from utils.database_utils import validate_user_exists
        await validate_user_exists(get_database(), str(interaction.user.id), interaction.user.display_name)

        # Create expedition record (guild percentage is now calculated based on actual distribution)
        actual_guild_percentage = (total_guild_sand_value / total_sand) * 100 if total_sand > 0 else 0
        expedition_id = await get_database().create_expedition(
            str(interaction.user.id),
            interaction.user.display_name,
            total_sand,
            sand_per_melange=int(conversion_rate),
            guild_cut_percentage=actual_guild_percentage
        )

        if not expedition_id:
            await send_response(interaction, "❌ Failed to create expedition record.", use_followup=use_followup, ephemeral=True)
            return

        # Add guild cut to treasury if > 0
        if guild_melange > 0 or guild_sand > 0:
            await get_database().update_guild_treasury(guild_sand, guild_melange)

            # Add guild transaction record for the guild cut
            await get_database().add_guild_transaction(
                transaction_type='guild_cut',
                sand_amount=guild_sand,
                melange_amount=guild_melange,
                expedition_id=expedition_id,
                admin_user_id=str(interaction.user.id),
                admin_username=interaction.user.display_name,
                description=f"Expedition #{expedition_id} guild cut"
            )

        # Process all participants
        participant_details = []

        for user_id, (user_melange, user_percentage) in unique_distributions.items():
            try:
                # Try to get user from guild first, then client
                try:
                    user = await interaction.guild.fetch_member(int(user_id))
                    display_name = user.display_name
                except (discord.NotFound, discord.HTTPException) as e:
                    logger.debug(f"User {user_id} not found in guild, trying client fetch: {e}")
                    try:
                        user = await interaction.client.fetch_user(int(user_id))
                        display_name = user.display_name
                    except (discord.NotFound, discord.HTTPException) as e:
                        logger.warning(f"User {user_id} not found via client fetch: {e}")
                        display_name = f"User_{user_id}"
            except ValueError as e:
                logger.error(f"Invalid user ID format: {user_id}, error: {e}")
                display_name = f"User_{user_id}"

            # Ensure user exists in database
            await validate_user_exists(get_database(), user_id, display_name)

            # Calculate equivalent sand for this user's melange (for deposit tracking)
            user_sand = int(user_melange * conversion_rate)

            # Add expedition participant
            await get_database().add_expedition_participant(
                expedition_id, user_id, display_name, user_sand,
                user_melange, is_harvester=False
            )

            # Add deposit record (using equivalent sand amount)
            await get_database().add_deposit(
                user_id,
                display_name,
                user_sand,
                deposit_type='group',
                expedition_id=expedition_id,
                melange_amount=user_melange,
                conversion_rate=conversion_rate
            )


            # Update user's melange total if they earned melange
            if user_melange > 0:
                await get_database().update_user_melange(user_id, user_melange)

                # Format for display
                percentage_text = f" ({user_percentage:.1f}%)" if user_percentage > 0 else ""
                participant_details.append(f"**{display_name}**: {user_melange:,} melange{percentage_text}")

        # Build response embed
        from utils.embed_utils import build_status_embed

        fields = {
            "👥 Participants": "\n".join(participant_details),
            "🏛️ Guild Cut": f"**{actual_guild_percentage:.1f}%** ({display_guild_sand:,} sand value) = **{guild_melange:,} melange** + {guild_sand:,} sand",
            "📊 Summary": f"**Total:** {total_sand:,} sand → **{total_melange:,} melange** | **Users:** **{total_user_melange:,} melange** | **Guild:** **{guild_melange:,} melange**"
        }

        embed = build_status_embed(
            title="🏜️ Expedition Split Completed",
            description=f"**Expedition #{expedition_id}** - {len(unique_distributions)} participants",
            color=0x00FF00,
            fields=fields,
            timestamp=interaction.created_at
        )

        # Send response
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)

        # Log the expedition creation
        logger.info(f"Expedition {expedition_id} created by {interaction.user.display_name} ({interaction.user.id})",
                   total_sand=total_sand, total_melange=total_melange, guild_melange=guild_melange,
                   guild_sand=guild_sand, participants=len(unique_distributions))

    except Exception as error:
        logger.error(f"Error in split command: {error}")
        logger.error(f"Split command traceback: {traceback.format_exc()}")

        try:
            await send_response(interaction, "❌ An error occurred while processing the split. Please try again.", use_followup=use_followup, ephemeral=True)
        except Exception as response_error:
            logger.error(f"Failed to send error response: {response_error}")
