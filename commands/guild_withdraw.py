"""
Guild Withdraw command for transferring sand from guild treasury to users (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': [],  # ['withdraw'] - removed for simplicity
    'description': "Withdraw sand from guild treasury to give to a user (Admin/Officer only)",
    'params': {
        'user': "User to give sand to",
        'amount': "Amount of sand to withdraw from guild treasury"
    },
    'permission_level': 'admin_or_officer'
}

import time
import discord
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import get_database, send_response
from utils.base_command import admin_command
from utils.logger import logger


@admin_command('guild_withdraw')
async def guild_withdraw(interaction, command_start, user: discord.Member, amount: int, use_followup: bool = True):
    """Withdraw sand from guild treasury and give to a user (Admin only)"""

    try:
        # Validate amount
        if amount < 1:
            await send_response(interaction, "❌ Withdrawal amount must be at least 1 sand.", use_followup=use_followup, ephemeral=True)
            return

        # Get current guild treasury balance
        treasury_data, get_treasury_time = await timed_database_operation(
            "get_guild_treasury",
            get_database().get_guild_treasury
        )

        current_sand = treasury_data.get('total_sand', 0)
        if current_sand < amount:
            await send_response(interaction,
                f"❌ Insufficient guild treasury funds.\n\n"
                f"**Available:** {current_sand:,} sand\n"
                f"**Requested:** {amount:,} sand\n"
                f"**Shortfall:** {amount - current_sand:,} sand",
                use_followup=use_followup, ephemeral=True)
            return

        # Perform withdrawal
        _, withdraw_time = await timed_database_operation(
            "guild_withdraw",
            get_database().guild_withdraw,
            str(interaction.user.id), interaction.user.display_name,
            str(user.id), user.display_name, amount
        )

        # Get updated treasury balance
        updated_treasury, _ = await timed_database_operation(
            "get_guild_treasury",
            get_database().get_guild_treasury
        )

        # Build response embed
        fields = {
            "💸 Transaction": f"**Recipient:** {user.display_name} | **Amount:** {amount:,} sand | **Admin:** {interaction.user.display_name}",
            "🏛️ Treasury": f"**Previous:** {current_sand:,} | **New:** {updated_treasury.get('total_sand', 0):,} | **Available:** {updated_treasury.get('total_sand', 0):,}"
        }

        embed = build_status_embed(
            title="✅ Guild Withdrawal Completed",
            description=f"💰 **{amount:,} sand** transferred from guild treasury to **{user.display_name}**",
            color=0x00FF00,
            fields=fields,
            timestamp=interaction.created_at
        )

        # Send response
        response_start = time.time()
        await send_response(interaction, embed=embed.build(), use_followup=use_followup)
        response_time = time.time() - response_start

        # Log metrics
        total_time = time.time() - command_start
        log_command_metrics(
            "Guild Withdraw",
            str(interaction.user.id),
            interaction.user.display_name,
            total_time,
            admin_id=str(interaction.user.id),
            admin_username=interaction.user.display_name,
            target_user_id=str(user.id),
            target_username=user.display_name,
            get_treasury_time=f"{get_treasury_time:.3f}s",
            withdraw_time=f"{withdraw_time:.3f}s",
            response_time=f"{response_time:.3f}s",
            withdrawal_amount=amount,
            previous_balance=current_sand,
            new_balance=updated_treasury.get('total_sand', 0)
        )

        # Log the withdrawal for audit
        logger.info(f"Guild withdrawal: {amount:,} sand from treasury to {user.display_name} ({user.id}) by {interaction.user.display_name} ({interaction.user.id})")

    except ValueError as ve:
        # Handle insufficient funds or other validation errors
        await send_response(interaction, f"❌ {str(ve)}", use_followup=use_followup, ephemeral=True)

    except Exception as error:
        total_time = time.time() - command_start
        logger.error(f"Error in guild_withdraw command: {error}",
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    target_user_id=str(user.id),
                    target_username=user.display_name,
                    amount=amount,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, "❌ An error occurred while processing the withdrawal.", use_followup=use_followup, ephemeral=True)
