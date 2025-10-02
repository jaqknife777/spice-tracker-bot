"""
Permission utilities for the Spice Tracker Bot.
"""
import os
import discord
from typing import Callable, Any, Set
from functools import wraps
from utils.helpers import get_admin_roles, get_officer_roles, get_user_roles


def _get_command_permission_level(command_name: str) -> str:
    """
    Get the permission level for a command without circular import.
    This is a simplified version that doesn't depend on the commands package.
    """
    # Default permission levels for known commands
    admin_commands = {'reset', 'pending', 'payroll', 'pay', 'guild_withdraw'}
    user_commands = {'sand', 'refinery', 'treasury', 'ledger', 'expedition', 'split', 'water', 'leaderboard'}
    any_commands = {'help', 'perms', 'calc'}

    if command_name in admin_commands:
        return 'admin'
    elif command_name in user_commands:
        return 'user'
    elif command_name in any_commands:
        return 'any'
    else:
        return 'user'  # Default to user level


def _get_user_role_id_set(interaction: discord.Interaction) -> Set[int]:
    """Extracts a set of role IDs from the user in the interaction."""
    if hasattr(interaction.user, 'roles') and interaction.user.roles:
        return {role.id for role in interaction.user.roles}
    return set()


def is_admin(interaction: discord.Interaction) -> bool:
    """
    Check if user has admin permissions.
    An admin is either the bot owner or has a cached admin role.
    """
    # Check if the user is the bot owner
    try:
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if interaction.user.id == owner_id:
            return True
    except (ValueError, TypeError):
        pass  # Ignore if BOT_OWNER_ID is not a valid integer

    # Check for admin roles
    admin_role_ids = get_admin_roles()
    if not admin_role_ids:
        return False  # Owner check failed and no roles are set

    user_role_ids = _get_user_role_id_set(interaction)
    return any(role_id in user_role_ids for role_id in admin_role_ids)


def is_user(interaction: discord.Interaction) -> bool:
    """
    Check if user is allowed to use the bot based on cached user roles.
    Returns True if no role restrictions OR user has allowed roles.
    """
    config_user_roles = get_user_roles()

    # If no role restrictions, allow all users
    if not config_user_roles:
        return True

    user_role_ids = _get_user_role_id_set(interaction)
    return any(role_id in user_role_ids for role_id in config_user_roles)


def is_officer(interaction: discord.Interaction) -> bool:
    """
    Check if user has officer permissions based on cached officer roles.
    Returns True only if user has one of the specified officer role IDs.
    """
    officer_role_ids = get_officer_roles()

    # If no officer roles configured, deny access (no officers)
    if not officer_role_ids:
        return False

    user_role_ids = _get_user_role_id_set(interaction)
    return any(role_id in user_role_ids for role_id in officer_role_ids)


def check_permission(interaction: discord.Interaction, permission_level: str) -> bool:
    """
    Check if user has the required permission level.

    Args:
        interaction: Discord interaction object
        permission_level: Required permission level ('admin', 'officer', 'admin_or_officer', 'user', 'any')

    Returns:
        True if user has required permission, False otherwise
    """
    if permission_level == 'admin':
        return is_admin(interaction)
    elif permission_level == 'officer':
        return is_officer(interaction)
    elif permission_level == 'admin_or_officer':
        return is_admin(interaction) or is_officer(interaction)
    elif permission_level == 'user':
        # Admins and officers should always have access to user-level commands
        return is_admin(interaction) or is_officer(interaction) or is_user(interaction)
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
        'admin_or_officer': "❌ You need an admin or officer role to use this command. Contact a server administrator.",
        'user': "❌ You don't have permission to use this command. Use `/perms` to check your permission status.",
        'any': "❌ You don't have permission to use this command."
    }

    return permission_messages.get(permission_level, "❌ You don't have permission to use this command.")
