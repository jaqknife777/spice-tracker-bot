"""
Permission utilities for the Spice Tracker Bot.
"""

import os
import discord
from typing import List, Callable, Any
from functools import wraps

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


def _get_command_permission_level(command_name: str) -> str:
    """
    Get the permission level for a command without circular import.
    This is a simplified version that doesn't depend on the commands package.
    """
    # Default permission levels for known commands
    admin_commands = {'reset', 'pending', 'payroll', 'payment', 'guild_withdraw'}
    user_commands = {'sand', 'refinery', 'treasury', 'leaderboard', 'ledger', 'expedition', 'split', 'water'}
    any_commands = {'help'}

    if command_name in admin_commands:
        return 'admin'
    elif command_name in user_commands:
        return 'user'
    elif command_name in any_commands:
        return 'any'
    else:
        return 'user'  # Default to user level

def get_admin_role_ids() -> List[int]:
    """Get admin role IDs from environment variable"""
    return _parse_role_ids(os.getenv('ADMIN_ROLE_IDS', ''))

def get_allowed_role_ids() -> List[int]:
    """Get allowed role IDs from environment variable"""
    return _parse_role_ids(os.getenv('ALLOWED_ROLE_IDS', ''))

def get_officer_role_ids() -> List[int]:
    """Get officer role IDs from environment variable"""
    return _parse_role_ids(os.getenv('OFFICER_ROLE_IDS', ''))

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

def is_officer(interaction: discord.Interaction) -> bool:
    """
    Check if user has officer permissions based on OFFICER_ROLE_IDS environment variable.
    Returns True only if user has one of the specified officer role IDs.
    """
    officer_role_ids = get_officer_role_ids()

    # If no officer roles configured, deny access (no officers)
    if not officer_role_ids:
        return False

    # Check if user has any of the specified officer roles
    if hasattr(interaction.user, 'roles'):
        user_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in user_role_ids for role_id in officer_role_ids)

    return False

def check_permission(interaction: discord.Interaction, permission_level: str) -> bool:
    """
    Check if user has the required permission level.

    Args:
        interaction: Discord interaction object
        permission_level: Required permission level ('admin', 'officer', 'user', 'any')

    Returns:
        True if user has required permission, False otherwise
    """
    if permission_level == 'admin':
        return is_admin(interaction)
    elif permission_level == 'officer':
        return is_officer(interaction)
    elif permission_level == 'user':
        return is_allowed_user(interaction)
    elif permission_level == 'any':
        return True
    else:
        # Unknown permission level, deny access
        return False

def require_permission_from_metadata():
    """
    Decorator that automatically reads permission level from command metadata.
    This eliminates duplication between decorator and metadata.

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs) -> Any:
            # Get the command name from the function name
            command_name = func.__name__

            from utils.helpers import send_response

            # Get permission level from metadata (avoiding circular import)
            permission_level = _get_command_permission_level(command_name)

            # Check permission before executing command
            if not check_permission(interaction, permission_level):
                message = get_permission_denied_message(permission_level)
                await send_response(interaction, message, use_followup=kwargs.get('use_followup', True), ephemeral=True)
                return

            # Execute the original function
            return await func(interaction, *args, **kwargs)

        return wrapper
    return decorator

def require_permission(permission_level: str):
    """
    Legacy decorator to require specific permission level for command execution.
    DEPRECATED: Use require_permission_from_metadata() instead.

    Args:
        permission_level: Required permission level ('admin', 'officer', 'user', 'any')

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs) -> Any:
            # Check permission before executing command
            if not check_permission(interaction, permission_level):
                # Import here to avoid circular imports
                from utils.helpers import send_response

                message = get_permission_denied_message(permission_level)
                await send_response(interaction, message, use_followup=kwargs.get('use_followup', True), ephemeral=True)
                return

            # Execute the original function
            return await func(interaction, *args, **kwargs)

        return wrapper
    return decorator

def validate_command_permission(interaction: discord.Interaction, command_metadata: dict) -> bool:
    """
    Validate if user has permission to execute a command based on its metadata.

    Args:
        interaction: Discord interaction object
        command_metadata: Command metadata dictionary containing permission_level

    Returns:
        True if user has permission, False otherwise
    """
    permission_level = command_metadata.get('permission_level', 'user')  # Default to 'user' if not specified
    return check_permission(interaction, permission_level)

def get_permission_denied_message(permission_level: str) -> str:
    """
    Get the appropriate permission denied message for a permission level.

    Args:
        permission_level: The permission level that was required

    Returns:
        Appropriate error message
    """
    permission_messages = {
        'admin': "❌ You need an admin role to use this command. Contact a server administrator.",
        'officer': "❌ You need an officer role to use this command. Contact a server administrator.",
        'user': "❌ You don't have permission to use this command.",
        'any': "❌ You don't have permission to use this command."
    }

    return permission_messages.get(permission_level, "❌ You don't have permission to use this command.")
