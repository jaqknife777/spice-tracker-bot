"""
Permission utilities for the Spice Tracker Bot.
"""

import os
import discord
from typing import List

def _parse_role_ids(env_var: str) -> List[int]:
    """Parse comma-separated role IDs from environment variable"""
    if not env_var:
        return []
    
    try:
        role_ids = []
        for role_id in env_var.split(','):
            role_id = role_id.strip()
            if role_id and role_id.isdigit():
                role_ids.append(int(role_id))
        return role_ids
    except ValueError:
        return []

def get_admin_role_ids() -> List[int]:
    """Get admin role IDs from environment variable"""
    return _parse_role_ids(os.getenv('ADMIN_ROLE_IDS', ''))

def get_allowed_role_ids() -> List[int]:
    """Get allowed role IDs from environment variable"""
    return _parse_role_ids(os.getenv('ALLOWED_ROLE_IDS', ''))

def is_admin(interaction: discord.Interaction) -> bool:
    """
    Check if user has admin permissions based on ADMIN_ROLE_IDS environment variable.
    Returns True only if user has one of the specified admin role IDs.
    """
    admin_role_ids = get_admin_role_ids()
    
    # If no admin roles configured, deny access (no admins)
    if not admin_role_ids:
        return False
    
    # Check if user has any of the specified admin roles
    if hasattr(interaction.user, 'roles'):
        user_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in user_role_ids for role_id in admin_role_ids)
    
    return False

def is_allowed_user(interaction: discord.Interaction) -> bool:
    """
    Check if user is allowed to use the bot.
    Returns True if no role restrictions OR user has allowed roles.
    """
    allowed_role_ids = get_allowed_role_ids()
    
    # If no role restrictions, allow all users
    if not allowed_role_ids:
        return True
    
    # Check if user has any allowed roles
    if hasattr(interaction.user, 'roles'):
        user_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in user_role_ids for role_id in allowed_role_ids)
    
    return False