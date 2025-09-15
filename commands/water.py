"""
Water delivery request command for guild members.
"""

import time
from utils.embed_utils import build_info_embed, build_status_embed
from utils.command_utils import log_command_metrics
from utils.base_command import command
from utils.helpers import send_response, build_admin_officer_role_mentions
from utils.logger import logger

# Command metadata
COMMAND_METADATA = {
    'aliases': ['delivery', 'water_delivery'],
    'description': "Request a water delivery to a specific location",
    'permission_level': 'user'
}


@command('water')
async def water(interaction, command_start, destination: str = "DD base", use_followup: bool = True):
    """Request a water delivery to a specific location"""

    # Validate destination (basic sanitization)
    destination = destination.strip()
    if len(destination) > 100:
        destination = destination[:100] + "..."

    if not destination:
        destination = "DD base"

    # Create water request embed
    embed = build_status_embed(
        title="💧 Water Delivery Request",
        description=f"**Location:** {destination}",
        color=0x3498DB,
        fields={
            "👤 Requester": f"{interaction.user.mention}",
            "📍 Destination": destination,
            "⏰ Requested": f"<t:{int(time.time())}:R>",
            "📋 Status": "⏳ Pending admin approval"
        },
        thumbnail=interaction.user.display_avatar.url,
        timestamp=interaction.created_at if hasattr(interaction.created_at, 'timestamp') else None
    )

    # Send the water request message
    response_start = time.time()
    # Send a single message containing the role mentions and the embed
    mentions_text = build_admin_officer_role_mentions()
    await send_response(interaction, content=mentions_text if mentions_text else None, embed=embed.build(), use_followup=use_followup, ephemeral=False)
    response_time = time.time() - response_start

    # Add checkmark reaction for admin approval
    # We need to get the message from the channel since send_response doesn't return it
    try:
        # Get the last message in the channel (which should be our water request)
        async for message in interaction.channel.history(limit=1):
            if message.author == interaction.client.user and message.embeds:
                await message.add_reaction("✅")
                break
    except Exception as e:
        # If we can't add the reaction, log it but don't fail the command
        logger.warning(f"Could not add reaction to water request: {e}")

    # Log performance metrics
    total_time = time.time() - command_start
    log_command_metrics(
        "Water",
        str(interaction.user.id),
        interaction.user.display_name,
        total_time,
        response_time=f"{response_time:.3f}s",
        destination=destination,
        guild_id=interaction.guild.id if interaction.guild else None,
        guild_name=interaction.guild.name if interaction.guild else None
    )
