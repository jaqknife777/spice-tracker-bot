"""
Commands package for the Spice Tracker Bot.
Contains all the individual command implementations.
"""

# Import all command functions
from .harvest import harvest, COMMAND_METADATA as harvest_metadata
from .refinery import refinery, COMMAND_METADATA as refinery_metadata
from .leaderboard import leaderboard, COMMAND_METADATA as leaderboard_metadata
from .conversion import conversion, COMMAND_METADATA as conversion_metadata
from .split import split, COMMAND_METADATA as split_metadata
from .help import help_command, COMMAND_METADATA as help_metadata
from .reset import reset, COMMAND_METADATA as reset_metadata
from .ledger import ledger, COMMAND_METADATA as ledger_metadata
from .expedition import expedition_details, COMMAND_METADATA as expedition_metadata
from .payment import payment, COMMAND_METADATA as payment_metadata
from .payroll import payroll, COMMAND_METADATA as payroll_metadata

# Export all command functions
__all__ = [
    'harvest',
    'refinery', 
    'leaderboard',
    'conversion',
    'split',
    'help_command',
    'reset',
    'ledger',
    'expedition_details',
    'payment',
    'payroll'
]

# Export all command metadata
COMMAND_METADATA = {
    'harvest': harvest_metadata,
    'refinery': refinery_metadata,
    'leaderboard': leaderboard_metadata,
    'conversion': conversion_metadata,
    'split': split_metadata,
    'help': help_metadata,
    'reset': reset_metadata,
    'ledger': ledger_metadata,
    'expedition': expedition_metadata,
    'payment': payment_metadata,
    'payroll': payroll_metadata
}
