"""
Commands package for the Spice Tracker Bot.
Contains all the individual command implementations.
"""

import os
import importlib

# Automatically discover and import all command modules
def discover_commands():
    """Automatically discover all command modules in this package"""
    commands = {}
    metadata = {}
    
    # Get the directory this file is in
    current_dir = os.path.dirname(__file__)
    
    # Find all .py files (excluding __init__.py and __pycache__)
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]  # Remove .py extension
            
            try:
                # Import the module
                module = importlib.import_module(f'.{module_name}', package=__name__)
                
                # Get the command function (same name as module)
                command_func = getattr(module, module_name, None)
                if command_func:
                    commands[module_name] = command_func
                
                # Get the metadata
                command_metadata = getattr(module, 'COMMAND_METADATA', None)
                if command_metadata:
                    metadata[module_name] = command_metadata
                    
            except ImportError as e:
                print(f"Warning: Could not import {module_name}: {e}")
    
    return commands, metadata

# Auto-discover commands and metadata
COMMANDS, COMMAND_METADATA = discover_commands()

# Export all discovered commands
__all__ = list(COMMANDS.keys())

# Export all discovered metadata
COMMAND_METADATA = COMMAND_METADATA
