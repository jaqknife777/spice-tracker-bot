"""
Perms command: show the caller's permission flags and relevant role matches.
"""

from utils.base_command import command
from utils.helpers import send_response
from utils.embed_utils import build_status_embed
from utils.permissions import (
    is_admin,
    is_officer,
    is_allowed_user,
    get_admin_role_ids,
    get_officer_role_ids,
    get_allowed_role_ids,
)


# Command metadata
COMMAND_METADATA = {
    'aliases': [],
    'description': "Show your permission status (admin, officer, user) and matched roles",
    'permission_level': 'any',
}


@command('perms')
async def perms(interaction, command_start, use_followup: bool = True):
    """Display the user's permission flags and role matches for this server."""

    # Compute permission flags
    admin_flag = is_admin(interaction)
    officer_flag = is_officer(interaction)
    user_flag = is_allowed_user(interaction)
    admin_or_officer_flag = admin_flag or officer_flag

    # Gather configured role IDs
    configured_admin_roles = get_admin_role_ids()
    configured_officer_roles = get_officer_role_ids()
    configured_allowed_roles = get_allowed_role_ids()

    # Determine role matches on the user
    user_role_ids = []
    user_role_names = []
    matched_admin_roles = []
    matched_officer_roles = []
    matched_allowed_roles = []

    if hasattr(interaction.user, 'roles') and interaction.user.roles:
        user_role_ids = [getattr(role, 'id', None) for role in interaction.user.roles if hasattr(role, 'id')]
        user_role_names = [getattr(role, 'name', str(getattr(role, 'id', 'unknown'))) for role in interaction.user.roles]

        matched_admin_roles = [str(rid) for rid in user_role_ids if rid in configured_admin_roles]
        matched_officer_roles = [str(rid) for rid in user_role_ids if rid in configured_officer_roles]
        matched_allowed_roles = [str(rid) for rid in user_role_ids if rid in configured_allowed_roles]

    # Build fields for the embed
    fields = {
        "🔐 Permission Flags": (
            f"**admin:** {'✅' if admin_flag else '❌'}\n"
            f"**officer:** {'✅' if officer_flag else '❌'}\n"
            f"**admin_or_officer:** {'✅' if admin_or_officer_flag else '❌'}\n"
            f"**user:** {'✅' if user_flag else '❌'}\n"
            f"**any:** ✅"
        ),
        "🧩 Configured Role IDs": (
            f"admins: {', '.join(map(str, configured_admin_roles)) if configured_admin_roles else '—'}\n"
            f"officers: {', '.join(map(str, configured_officer_roles)) if configured_officer_roles else '—'}\n"
            f"allowed: {', '.join(map(str, configured_allowed_roles)) if configured_allowed_roles else '— (all users)'}"
        ),
        "🧑 Your Roles": (
            f"names: {', '.join(user_role_names) if user_role_names else '—'}\n"
            f"ids: {', '.join(map(str, user_role_ids)) if user_role_ids else '—'}"
        ),
        "✅ Matches": (
            f"admin roles: {', '.join(matched_admin_roles) if matched_admin_roles else '—'}\n"
            f"officer roles: {', '.join(matched_officer_roles) if matched_officer_roles else '—'}\n"
            f"allowed roles: {', '.join(matched_allowed_roles) if matched_allowed_roles else '—'}"
        ),
    }

    embed = build_status_embed(
        title="Your Permission Status",
        description=f"User: **{interaction.user.display_name}**",
        fields=fields,
        color=0x7289DA,
    )

    await send_response(interaction, embed=embed.build(), use_followup=use_followup)
