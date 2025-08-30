"""
Permission utilities for the Spice Tracker Bot.
Currently minimal implementation - expand as needed for future role-based permissions.
"""

import os
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

# Note: Additional permission functions can be added here as needed
# Current implementation is minimal since role-based permissions are not yet used