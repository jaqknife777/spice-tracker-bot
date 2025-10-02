"""
Helper functions used across multiple commands.
"""

import os
import re
from typing import List, Optional, Union
from database_orm import Database
from utils.logger import logger
# Initialize database (lazy initialization)
database = None

def get_database():
    """Get or create database instance"""
    global database
    if database is None:
        database = Database()
    return database

def parse_roles(roles_str: str) -> List[int]:
    """
    Parses a string of role IDs and role mentions into a list of unique integer role IDs.
    Supports comma-separated IDs and space-separated mentions.
    """
    if not roles_str:
        return []

    # Find all numbers (for raw IDs) and all mentions (for <@&ID>)
    raw_ids = re.findall(r'\d+', roles_str)

    # Convert to a set of integers to get unique IDs, then to a sorted list.
    return sorted(list(set(map(int, raw_ids))))


# Sand to melange conversion rates (implementation detail)
SAND_PER_MELANGE_NORMAL = 50
SAND_PER_MELANGE_LANDSRAAD = 37.5

def get_sand_per_melange() -> int:
    """Get the spice sand to melange conversion rate (hardcoded constant) - DEPRECATED"""
    return SAND_PER_MELANGE_NORMAL

# Global variables to cache settings
_landsraad_bonus_active = False
_user_cut: Optional[int] = None
_guild_cut: int = 10
_region: Optional[str] = None
_admin_role_ids: List[int] = []
_officer_role_ids: List[int] = []
_user_role_ids: List[int] = []


async def initialize_global_settings():
    """Called once when the bot starts up to load all global settings."""
    global _landsraad_bonus_active, _user_cut, _guild_cut, _region, _admin_role_ids, _officer_role_ids, _user_role_ids
    logger.info("Initializing global settings from database...")
    try:
        db = get_database()
        settings = await db.get_all_global_settings()

        # Landsraad Bonus
        landsraad_status_str = settings.get('landsraad_bonus_active')
        _landsraad_bonus_active = landsraad_status_str is not None and landsraad_status_str.lower() == 'true'
        logger.info(f"Initial Landsraad bonus status loaded: {_landsraad_bonus_active}")

        # User Cut
        user_cut_val = settings.get('user_cut')
        if user_cut_val and user_cut_val.isdigit() and int(user_cut_val) != 0:
            _user_cut = int(user_cut_val)
        else:
            _user_cut = None
        logger.info(f"Initial user_cut loaded: {_user_cut}")

        # Guild Cut
        guild_cut_val = settings.get('guild_cut')
        if guild_cut_val and guild_cut_val.isdigit() and int(guild_cut_val) != 0:
            _guild_cut = int(guild_cut_val)
        else:
            _guild_cut = 10 # Default value
        logger.info(f"Initial guild_cut loaded: {_guild_cut}")

        # Region
        region_val = settings.get('region')
        _region = region_val if region_val else None
        logger.info(f"Initial region loaded: {_region}")

        # Role settings
        _admin_role_ids = parse_roles(settings.get('admin_roles', ''))
        logger.info(f"Initial admin roles loaded: {_admin_role_ids}")
        _officer_role_ids = parse_roles(settings.get('officer_roles', ''))
        logger.info(f"Initial officer roles loaded: {_officer_role_ids}")
        _user_role_ids = parse_roles(settings.get('user_roles', ''))
        logger.info(f"Initial user roles loaded: {_user_role_ids}")


    except Exception as e:
        logger.error(f"Error initializing global settings: {e}", exc_info=True)
        # Ensure defaults are set on error
        _landsraad_bonus_active = False
        _user_cut = None
        _guild_cut = 10
        _region = None
        _admin_role_ids = []
        _officer_role_ids = []
        _user_role_ids = []
        logger.warning("Global settings initialization failed. Using default values.")

def is_landsraad_bonus_active():
    """Reads the bonus status from the in-memory cache."""
    return _landsraad_bonus_active

def update_landsraad_bonus_status(new_status: bool):
    """Updates the in-memory cache."""
    global _landsraad_bonus_active
    _landsraad_bonus_active = new_status
    logger.info(f"Landsraad bonus status updated in cache: {new_status}")


def get_user_cut() -> Optional[int]:
    """Reads the user_cut from the in-memory cache."""
    return _user_cut

def update_user_cut(new_value: Optional[int]):
    """Updates the in-memory cache for user_cut, treating 0 as None."""
    global _user_cut
    _user_cut = new_value if new_value and new_value != 0 else None
    logger.info(f"User cut updated in cache: {_user_cut}")

def get_guild_cut() -> int:
    """Reads the guild_cut from the in-memory cache."""
    return _guild_cut

def update_guild_cut(new_value: Optional[int]):
    """Updates the in-memory cache for guild_cut, treating 0 or None as 10."""
    global _guild_cut
    _guild_cut = new_value if new_value and new_value != 0 else 10
    logger.info(f"Guild cut updated in cache: {_guild_cut}")

def get_region() -> Optional[str]:
    """Reads the region from the in-memory cache."""
    return _region

def update_region(new_value: Optional[str]):
    """Updates the in-memory cache for region."""
    global _region
    _region = new_value
    logger.info(f"Region updated in cache: {_region}")

def get_admin_roles() -> List[int]:
    """Reads the admin_roles from the in-memory cache."""
    return _admin_role_ids

def update_admin_roles(new_roles: List[int]):
    """Updates the in-memory cache for admin_roles."""
    global _admin_role_ids
    _admin_role_ids = new_roles
    logger.info(f"Admin roles updated in cache: {new_roles}")

def get_officer_roles() -> List[int]:
    """Reads the officer_roles from the in-memory cache."""
    return _officer_role_ids

def update_officer_roles(new_roles: List[int]):
    """Updates the in-memory cache for officer_roles."""
    global _officer_role_ids
    _officer_role_ids = new_roles
    logger.info(f"Officer roles updated in cache: {new_roles}")

def get_user_roles() -> List[int]:
    """Reads the user_roles from the in-memory cache."""
    return _user_role_ids

def update_user_roles(new_roles: List[int]):
    """Updates the in-memory cache for user_roles."""
    global _user_role_ids
    _user_role_ids = new_roles
    logger.info(f"User roles updated in cache: {new_roles}")


async def get_sand_per_melange_with_bonus() -> float:
    """Get the current sand to melange conversion rate, considering landsraad bonus"""
    if is_landsraad_bonus_active():
        return SAND_PER_MELANGE_LANDSRAAD
    else:
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

async def send_response(interaction, content=None, embed=None, view=None, ephemeral=False, use_followup=True):
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

    kwargs = {}
    if content:
        kwargs['content'] = content
    if embed:
        kwargs['embed'] = embed
    if view:
        kwargs['view'] = view
    if ephemeral:
        kwargs['ephemeral'] = ephemeral

    try:
        if use_followup:
            await interaction.followup.send(**kwargs)
        else:
            # remove ephemeral for channel.send, as it is not supported
            kwargs.pop('ephemeral', None)
            await interaction.channel.send(**kwargs)

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
            if embed is not None and content is None:
                await interaction.channel.send(embed=embed)
            elif embed is None and content is not None:
                await interaction.channel.send(content)
            elif embed is not None and content is not None:
                await interaction.channel.send(content=content, embed=embed)

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
    try:
        admin_role_ids: List[int] = get_admin_roles()
        officer_role_ids: List[int] = get_officer_roles()

        # Combine and deduplicate role IDs
        role_ids = sorted(list(set(admin_role_ids + officer_role_ids)))

        if not role_ids:
            return ""

        return " ".join([f"<@&{rid}>" for rid in role_ids])
    except Exception as e:
        logger.warning(f"Failed to build admin/officer role mentions: {e}")
        return ""

def format_melange(amount: float) -> str:
    """Formats melange amount, removing .00 for whole numbers."""
    if amount == int(amount):
        return f"{int(amount):,}"
    else:
        return f"{amount:,.2f}"


def format_roles(role_ids: List[Union[int, str]]) -> List[str]:
    """
    Formats a list of role IDs into a list of Discord role mentions.

    Args:
        role_ids: A list of role IDs (can be integers or strings).

    Returns:
        A list of formatted role mention strings.
    """
    return [f"<@&{rid}>" for rid in role_ids]
