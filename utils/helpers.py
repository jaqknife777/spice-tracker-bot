"""
Helper functions used across multiple commands.
"""

import os
from typing import List
from database_orm import Database

# Initialize database (lazy initialization)
database = None

def get_database():
    """Get or create database instance"""
    global database
    if database is None:
        database = Database()
    return database

# Sand to melange conversion rates (implementation detail)
SAND_PER_MELANGE_NORMAL = 50
SAND_PER_MELANGE_LANDSRAAD = 37.5

def get_sand_per_melange() -> int:
    """Get the spice sand to melange conversion rate (hardcoded constant) - DEPRECATED"""
    return SAND_PER_MELANGE_NORMAL

async def get_sand_per_melange_with_bonus() -> float:
    """Get the current sand to melange conversion rate, considering landsraad bonus"""
    try:
        db = get_database()
        is_active = await db.get_landsraad_bonus_status()

        # Explicitly check for True to handle any edge cases
        if is_active is True:
            return SAND_PER_MELANGE_LANDSRAAD
        else:
            return float(SAND_PER_MELANGE_NORMAL)
    except Exception as e:
        from utils.logger import logger
        logger.error(f"Error checking landsraad bonus status: {e}")
        # Default to normal rate if there's an error
        return float(SAND_PER_MELANGE_NORMAL)

async def convert_sand_to_melange(sand_amount: int) -> tuple[int, int]:
    """
    Convert sand amount to melange using current conversion rate.

    Args:
        sand_amount: Amount of sand to convert

    Returns:
        tuple: (melange_amount, remaining_sand)
    """
    conversion_rate = await get_sand_per_melange_with_bonus()

    # Handle fractional conversion rates (like 37.5)
    if conversion_rate == int(conversion_rate):
        # Integer conversion rate (normal case)
        melange_amount = sand_amount // int(conversion_rate)
        remaining_sand = sand_amount % int(conversion_rate)
    else:
        # Fractional conversion rate (landsraad bonus case)
        # Convert to integer melange and calculate remaining sand
        melange_amount = int(sand_amount / conversion_rate)
        remaining_sand = sand_amount - int(melange_amount * conversion_rate)

    return melange_amount, remaining_sand

async def send_response(interaction, content=None, embed=None, ephemeral=False, use_followup=True):
    """Helper function to send responses using the appropriate method based on use_followup"""
    import time
    from utils.logger import logger

    start_time = time.time()

    # Validate inputs with better error logging
    if not interaction:
        logger.error("send_response called with None interaction")
        return

    # Check if interaction has required attributes
    if not hasattr(interaction, 'channel') or not interaction.channel:
        logger.error(f"send_response called with invalid channel - interaction type: {type(interaction)}, channel: {getattr(interaction, 'channel', 'NO_CHANNEL_ATTR')}")
        return

    # Guild can be None for DMs, so we don't require it
    # But we do need to check if we're in a guild context for certain operations
    is_guild_context = hasattr(interaction, 'guild') and interaction.guild is not None

    try:
        if use_followup:
            if content is not None or embed is not None:
                await interaction.followup.send(content=content if content is not None else None, embed=embed, ephemeral=ephemeral)
        else:
            if content is not None or embed is not None:
                await interaction.channel.send(content=content if content is not None else None, embed=embed)

        response_time = time.time() - start_time
        logger.info(f"Response sent successfully",
                   response_time=f"{response_time:.3f}s",
                   use_followup=use_followup,
                   has_content=content is not None,
                   has_embed=embed is not None)

    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Error sending response: {e}",
                    response_time=f"{response_time:.3f}s",
                    use_followup=use_followup,
                    error=str(e))
        # Fallback to channel if followup fails
        try:
            if content is not None or embed is not None:
                await interaction.channel.send(content=content if content is not None else None, embed=embed)

            fallback_time = time.time() - start_time
            logger.info(f"Fallback response sent successfully",
                       total_time=f"{fallback_time:.3f}s",
                       fallback_time=f"{fallback_time - response_time:.3f}s")

        except Exception as fallback_error:
            total_time = time.time() - start_time
            logger.error(f"Fallback response also failed: {fallback_error}",
                        total_time=f"{total_time:.3f}s",
                        original_error=str(e),
                        fallback_error=str(fallback_error))
            # Last resort - just log the error, don't raise


def build_admin_officer_role_mentions() -> str:
    """Build a mention string for configured admin and officer roles.

    Returns:
        A space-separated string of role mentions like "<@&123> <@&456>", or an empty string
        if no roles are configured or on error.
    """
    from utils.logger import logger
    try:
        from utils.permissions import get_admin_role_ids, get_officer_role_ids

        admin_role_ids: List[int] = get_admin_role_ids()
        officer_role_ids: List[int] = get_officer_role_ids()

        role_ids: List[int] = []
        if admin_role_ids:
            role_ids.extend(admin_role_ids)
        if officer_role_ids:
            role_ids.extend(officer_role_ids)

        seen = set()
        mentions: List[str] = []
        for role_id in role_ids:
            if role_id not in seen:
                seen.add(role_id)
                mentions.append(f"<@&{role_id}>")

        return " ".join(mentions)
    except Exception as e:
        logger.warning(f"Failed to build admin/officer role mentions: {e}")
        return ""
