"""
Guild Withdraw command for transferring sand from guild treasury to users (Admin only).
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['withdraw'],
    'description': "Withdraw sand from guild treasury to give to a user (Admin only)",
    'params': {
        'user': "User to give sand to",
        'amount': "Amount of sand to withdraw from guild treasury"
    }
}

import time
import discord
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, send_response
from utils.logger import logger


@handle_interaction_expiration
async def guild_withdraw(interaction, user: discord.Member, amount: int, use_followup: bool = True):
    """Withdraw sand from guild treasury and give to a user (Admin only)"""
    command_start = time.time()
    
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await send_response(interaction, "❌ You need administrator permissions to use this command.", use_followup=use_followup, ephemeral=True)
        return
    
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
            "💸 Withdrawal Details": f"**Recipient:** {user.display_name}\n**Amount:** {amount:,} sand\n**Authorized by:** {interaction.user.display_name}",
            "🏛️ Updated Treasury": f"**Previous Balance:** {current_sand:,} sand\n**New Balance:** {updated_treasury.get('total_sand', 0):,} sand\n**Remaining:** {updated_treasury.get('total_sand', 0):,} sand available"
        }
        
        embed = build_status_embed(
            title="✅ Guild Withdrawal Completed",
            description=f"💰 **{amount:,} sand** transferred from guild treasury to **{user.display_name}**",
            color=0x00FF00,
            fields=fields,
            footer=f"Authorized by {interaction.user.display_name}",
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
