"""
Landsraad bonus command for managing the global melange conversion bonus.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['bonus'],
    'description': "Manage the landsraad bonus for melange conversion (37.5 sand = 1 melange)",
    'params': {
        'action': "Action to perform: 'status', 'enable', 'disable'",
        'confirm': "Confirmation required for enable/disable actions"
    },
    'permission_level': 'admin_or_officer'
}

import time
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import get_database, get_sand_per_melange_with_bonus, send_response
from utils.base_command import command
from utils.logger import logger


@command('landsraad')
async def landsraad(interaction, command_start, action: str, confirm: bool = False, use_followup: bool = True):
    """Manage the landsraad bonus for melange conversion"""

    # Validate action
    valid_actions = ['status', 'enable', 'disable']
    if action not in valid_actions:
        await send_response(interaction, f"❌ Invalid action. Use one of: {', '.join(valid_actions)}", use_followup=use_followup, ephemeral=True)
        return

    try:
        if action == 'status':
            # Get current status
            is_active, get_status_time = await timed_database_operation(
                "get_landsraad_bonus_status",
                get_database().get_landsraad_bonus_status
            )

            # Get current conversion rate
            conversion_rate = await get_sand_per_melange_with_bonus()

            status_text = "🟢 **ACTIVE**" if is_active else "🔴 **INACTIVE**"
            rate_text = f"{conversion_rate} sand = 1 melange"

            fields = {
                "📊 Status": status_text,
                "⚙️ Conversion Rate": rate_text,
                "💡 Effect": "37.5 sand = 1 melange" if is_active else "50 sand = 1 melange"
            }

            color = 0x00FF00 if is_active else 0xFF4500

            embed = build_status_embed(
                title="🏛️ Landsraad Bonus Status",
                description=f"Current melange conversion rate: **{rate_text}**",
                color=color,
                fields=fields,
                timestamp=interaction.created_at
            )

            await send_response(interaction, embed=embed.build(), use_followup=use_followup)

            # Log metrics
            total_time = time.time() - command_start
            log_command_metrics(
                "Landsraad Status",
                str(interaction.user.id),
                interaction.user.display_name,
                total_time,
                get_status_time=f"{get_status_time:.3f}s",
                is_active=is_active,
                conversion_rate=conversion_rate
            )

        elif action in ['enable', 'disable']:
            # Require confirmation for enable/disable
            if not confirm:
                action_text = "enable" if action == 'enable' else "disable"
                await send_response(
                    interaction,
                    f"⚠️ **Confirmation required!**\n\n"
                    f"Use `/landsraad {action} confirm:true` to {action_text} the landsraad bonus.\n\n"
                    f"**Effect:** This will change the conversion rate from 50 sand = 1 melange to 37.5 sand = 1 melange.",
                    use_followup=use_followup,
                    ephemeral=True
                )
                return

            # Set the status
            new_status = action == 'enable'
            _, set_status_time = await timed_database_operation(
                "set_landsraad_bonus_status",
                get_database().set_landsraad_bonus_status,
                new_status
            )

            # Get updated conversion rate
            conversion_rate = await get_sand_per_melange_with_bonus()

            action_text = "enabled" if new_status else "disabled"
            status_text = "🟢 **ACTIVE**" if new_status else "🔴 **INACTIVE**"
            rate_text = f"{conversion_rate} sand = 1 melange"

            fields = {
                "📊 Status": status_text,
                "⚙️ Conversion Rate": rate_text,
                "💡 Effect": "37.5 sand = 1 melange" if new_status else "50 sand = 1 melange"
            }

            color = 0x00FF00 if new_status else 0xFF4500

            embed = build_status_embed(
                title=f"🏛️ Landsraad Bonus {action_text.title()}",
                description=f"Melange conversion rate updated to: **{rate_text}**",
                color=color,
                fields=fields,
                timestamp=interaction.created_at
            )

            await send_response(interaction, embed=embed.build(), use_followup=use_followup)

            # Log metrics
            total_time = time.time() - command_start
            log_command_metrics(
                f"Landsraad {action.title()}",
                str(interaction.user.id),
                interaction.user.display_name,
                total_time,
                set_status_time=f"{set_status_time:.3f}s",
                new_status=new_status,
                conversion_rate=conversion_rate
            )

    except Exception as error:
        total_time = time.time() - command_start
        logger.error(f"Error in landsraad command: {error}",
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    action=action,
                    total_time=f"{total_time:.3f}s")
        await send_response(interaction, f"❌ An error occurred while managing landsraad bonus: {error}", use_followup=use_followup, ephemeral=True)
