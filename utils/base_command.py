"""
Base command class for the Spice Tracker Bot.
Provides common functionality and automatic permission handling.
"""

import time
from typing import Any, Callable, Dict, Optional
from abc import ABC, abstractmethod
from functools import wraps

import discord
from utils.decorators import handle_interaction_expiration
from utils.permissions import require_permission_from_metadata
from utils.helpers import send_response
from utils.logger import logger


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
        @require_permission_from_metadata()
        async def wrapper(interaction: discord.Interaction, *args, **kwargs) -> Any:
            # Start timing
            command_start = time.time()

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
