"""
Base command class for the Spice Tracker Bot.
Provides common functionality and automatic permission handling.
"""

import os
import time
from typing import Any, Callable, Dict, Optional
from abc import ABC, abstractmethod
from functools import wraps

import discord
from utils.decorators import handle_interaction_expiration
from utils.permissions import require_permission_from_metadata, check_permission
from utils.helpers import send_response
from utils.logger import logger


def get_permission_override(command_name: str) -> Optional[str]:
    """
    Get permission override for a specific command from environment variables.

    Environment variable format: COMMAND_PERMISSION_OVERRIDES
    Example: "reset:officer,sand:any,help:user"

    Args:
        command_name: Name of the command to check for overrides

    Returns:
        Override permission level if found, None otherwise
    """
    overrides_str = os.getenv('COMMAND_PERMISSION_OVERRIDES', '')
    if not overrides_str:
        return None

    try:
        # Parse comma-separated overrides
        overrides = {}
        for override in overrides_str.split(','):
            if ':' in override:
                cmd, permission = override.strip().split(':', 1)
                overrides[cmd.strip()] = permission.strip()

        return overrides.get(command_name)
    except Exception as e:
        logger.warning(f"Error parsing permission overrides: {e}")
        return None


def get_all_permission_overrides() -> Dict[str, str]:
    """
    Get all permission overrides from environment variables.

    Returns:
        Dictionary mapping command names to their override permission levels
    """
    overrides_str = os.getenv('COMMAND_PERMISSION_OVERRIDES', '')
    if not overrides_str:
        return {}

    try:
        overrides = {}
        for override in overrides_str.split(','):
            if ':' in override:
                cmd, permission = override.strip().split(':', 1)
                overrides[cmd.strip()] = permission.strip()
        return overrides
    except Exception as e:
        logger.warning(f"Error parsing permission overrides: {e}")
        return {}


def log_permission_overrides():
    """Log all active permission overrides for debugging."""
    overrides = get_all_permission_overrides()
    if overrides:
        logger.info(f"Permission overrides active: {overrides}")
    else:
        logger.debug("No permission overrides configured")


class BaseCommand(ABC):
    """
    Base class for all bot commands.
    Automatically handles permissions, timing, and common functionality.
    """

    def __init__(self, command_name: str):
        self.command_name = command_name

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator that wraps command functions with common functionality.
        """
        @wraps(func)
        @handle_interaction_expiration
        async def wrapper(interaction: discord.Interaction, *args, **kwargs) -> Any:
            # Start timing
            command_start = time.time()

            # Check for permission overrides first
            override_permission = get_permission_override(self.command_name)
            if override_permission:
                # Use override permission
                if not check_permission(interaction, override_permission):
                    from utils.permissions import get_permission_denied_message
                    message = get_permission_denied_message(override_permission)
                    await send_response(interaction, message, use_followup=kwargs.get('use_followup', True), ephemeral=True)
                    return
            else:
                # Use metadata-based permission checking
                from commands import get_command_permission_level
                permission_level = get_command_permission_level(self.command_name)
                if not check_permission(interaction, permission_level):
                    from utils.permissions import get_permission_denied_message
                    message = get_permission_denied_message(permission_level)
                    await send_response(interaction, message, use_followup=kwargs.get('use_followup', True), ephemeral=True)
                    return

            try:
                # Call the original function with timing context
                result = await func(interaction, command_start, *args, **kwargs)
                return result
            except Exception as error:
                # Log error and send user-friendly message
                total_time = time.time() - command_start
                logger.error(f"Error in {self.command_name} command: {error}",
                           command=self.command_name,
                           user_id=str(interaction.user.id),
                           username=interaction.user.display_name,
                           total_time=f"{total_time:.3f}s")

                await send_response(
                    interaction,
                    f"❌ An error occurred while executing the {self.command_name} command.",
                    use_followup=kwargs.get('use_followup', True),
                    ephemeral=True
                )
                raise

        return wrapper


class SimpleCommand(BaseCommand):
    """
    Simple command class for basic commands that don't need complex logic.
    """

    def __init__(self, command_name: str):
        super().__init__(command_name)


class AdminCommand(BaseCommand):
    """
    Admin command class with additional admin-specific functionality.
    """

    def __init__(self, command_name: str):
        super().__init__(command_name)

    def log_admin_action(self, interaction: discord.Interaction, action: str, **kwargs):
        """Log admin actions with additional context."""
        logger.info(f"Admin action: {action}",
                   admin_id=str(interaction.user.id),
                   admin_username=interaction.user.display_name,
                   command=self.command_name,
                   **kwargs)


# Decorator functions for easy use
def command(command_name: str):
    """
    Decorator to create a simple command.

    Usage:
        @command('sand')
        async def sand(interaction, amount: int, use_followup: bool = True):
            # Command logic here
    """
    cmd = SimpleCommand(command_name)
    return cmd

def admin_command(command_name: str):
    """
    Decorator to create an admin command.

    Usage:
        @admin_command('reset')
        async def reset(interaction, confirm: bool, use_followup: bool = True):
            # Admin command logic here
    """
    cmd = AdminCommand(command_name)
    return cmd
