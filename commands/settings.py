"""
Settings command group for managing bot settings.
"""
import time
import discord
from discord import app_commands
from typing import Literal, Optional, Any, Callable, Dict, List

# Import utility modules
from utils.database_utils import timed_database_operation
from utils.embed_utils import build_status_embed
from utils.command_utils import log_command_metrics
from utils.helpers import (
    get_database, get_sand_per_melange_with_bonus,
    send_response as original_send_response,
    update_landsraad_bonus_status,
    update_user_cut, get_user_cut,
    update_guild_cut, get_guild_cut,
    update_region, get_region,
    parse_roles, format_roles,
    get_admin_roles, update_admin_roles,
    get_officer_roles, update_officer_roles,
    get_user_roles, update_user_roles
)
from utils.logger import logger
from utils.permissions import check_permission

class Settings(app_commands.Group):
    """A command group for all settings-related commands."""
    def __init__(self, bot):
        super().__init__(name="settings", description="Manage bot settings")
        self.bot = bot

    async def send_response(self, interaction, *args, **kwargs):
        """Helper to handle response sending, since we are not using the @command decorator."""
        if not interaction.response.is_done():
            await interaction.response.send_message(*args, **kwargs)
        else:
            await interaction.followup.send(*args, **kwargs)

    async def _handle_role_setting(
        self,
        interaction: discord.Interaction,
        roles_str: Optional[str],
        *,
        setting_key: str,
        db_description: str,
        get_func: Callable[[], List[int]],
        update_func: Callable[[List[int]], None],
        permission_level: str,
        title: str,
        log_name: str,
    ):
        """Generic handler for viewing or setting a role-based global setting."""
        command_start = time.time()
        await interaction.response.defer(ephemeral=True)

        if not check_permission(interaction, permission_level):
            await self.send_response(interaction, "❌ You do not have permission to use this command.", ephemeral=True)
            return

        db = get_database()

        if roles_str is None:
            # View logic
            current_roles = get_func()
            role_mentions = format_roles(current_roles)
            description = f"Currently configured roles: {', '.join(role_mentions) if role_mentions else 'None'}"
            embed = build_status_embed(title=title, description=description, color=0x3498DB)
            await self.send_response(interaction, embed=embed.build())
        else:
            # Set logic
            try:
                parsed_roles = parse_roles(roles_str)
                db_value = ",".join(map(str, parsed_roles))

                await db.set_global_setting(setting_key, db_value, db_description)
                update_func(parsed_roles)

                role_mentions = format_roles(parsed_roles)
                description = f"Roles updated to: {', '.join(role_mentions) if role_mentions else 'None'}"
                embed = build_status_embed(title=f"✅ {title} Updated", description=description, color=0x00FF00)
                await self.send_response(interaction, embed=embed.build())

                log_command_metrics(f"Settings {log_name}", str(interaction.user.id), interaction.user.display_name, time.time() - command_start, new_value=parsed_roles)

            except Exception as e:
                logger.error(f"Error setting {setting_key}: {e}", user_id=str(interaction.user.id))
                await self.send_response(interaction, f"❌ An error occurred: {e}", ephemeral=True)

    @app_commands.command(name="admin_roles", description="Set or view the roles with admin permissions.")
    @app_commands.describe(roles="Comma-separated role IDs or @role mentions. Leave blank to view, or send empty to clear.")
    async def admin_roles(self, interaction: discord.Interaction, roles: Optional[str] = None):
        """Set or view the admin roles."""
        await self._handle_role_setting(
            interaction,
            roles,
            setting_key='admin_roles',
            db_description='Roles with admin permissions',
            get_func=get_admin_roles,
            update_func=update_admin_roles,
            permission_level='admin',
            title="👑 Admin Roles",
            log_name="AdminRoles"
        )

    @app_commands.command(name="officer_roles", description="Set or view the roles with officer permissions.")
    @app_commands.describe(roles="Comma-separated role IDs or @role mentions. Leave blank to view, or send empty to clear.")
    async def officer_roles(self, interaction: discord.Interaction, roles: Optional[str] = None):
        """Set or view the officer roles."""
        await self._handle_role_setting(
            interaction,
            roles,
            setting_key='officer_roles',
            db_description='Roles with officer permissions',
            get_func=get_officer_roles,
            update_func=update_officer_roles,
            permission_level='admin_or_officer',
            title="🛡️ Officer Roles",
            log_name="OfficerRoles"
        )

    @app_commands.command(name="user_roles", description="Set or view the roles allowed to use the bot.")
    @app_commands.describe(roles="Comma-separated role IDs or @role mentions. Leave blank to view, or send empty to clear.")
    async def user_roles(self, interaction: discord.Interaction, roles: Optional[str] = None):
        """Set or view the user roles."""
        await self._handle_role_setting(
            interaction,
            roles,
            setting_key='user_roles',
            db_description='Roles allowed to use the bot',
            get_func=get_user_roles,
            update_func=update_user_roles,
            permission_level='admin_or_officer',
            title="👥 User Roles",
            log_name="UserRoles"
        )

    @app_commands.command(name="landsraad", description="Manage the landsraad bonus for melange conversion")
    @app_commands.describe(
        action="Action to perform: 'status', 'enable', 'disable'",
        confirm="Confirmation required for enable/disable actions"
    )
    async def landsraad(self, interaction: discord.Interaction, action: Literal['status', 'enable', 'disable'], confirm: bool = False):
        """Manage the landsraad bonus for melange conversion"""
        command_start = time.time()
        await interaction.response.defer(ephemeral=True)

        if not check_permission(interaction, 'admin_or_officer'):
            await self.send_response(interaction, "❌ You do not have permission to use this command.", ephemeral=True)
            return

        try:
            db = get_database()
            if action == 'status':
                landsraad_status_str, get_status_time = await timed_database_operation(
                    "get_global_setting",
                    db.get_global_setting,
                    'landsraad_bonus_active'
                )
                is_active = landsraad_status_str and landsraad_status_str.lower() == 'true'

                conversion_rate = await get_sand_per_melange_with_bonus()
                status_text = "🟢 **ACTIVE**" if is_active else "🔴 **INACTIVE**"
                rate_text = f"{conversion_rate} sand = 1 melange"
                fields = {
                    "📊 Status": status_text,
                    "⚙️ Conversion Rate": rate_text,
                    "💡 Effect": "37.5 sand = 1 melange" if is_active else "50 sand = 1 melange"
                }
                color = 0x00FF00 if is_active else 0xFF4500
                embed = build_status_embed(
                    title="🏛️ Landsraad Bonus Status",
                    description=f"Current melange conversion rate: **{rate_text}**",
                    color=color,
                    fields=fields,
                    timestamp=interaction.created_at
                )
                await self.send_response(interaction, embed=embed.build())
                log_command_metrics(
                    "Landsraad Status", str(interaction.user.id), interaction.user.display_name, time.time() - command_start,
                    get_status_time=f"{get_status_time:.3f}s", is_active=is_active, conversion_rate=conversion_rate
                )

            elif action in ['enable', 'disable']:
                if not confirm:
                    action_text = "enable" if action == 'enable' else "disable"
                    await self.send_response(
                        interaction,
                        f"⚠️ **Confirmation required!**\n\n"
                        f"Use `/settings landsraad {action} confirm:true` to {action_text} the landsraad bonus.\n\n"
                        f"**Effect:** This will change the conversion rate.",
                        ephemeral=True
                    )
                    return

                new_status = action == 'enable'
                _, set_status_time = await timed_database_operation(
                    "set_global_setting",
                    db.set_global_setting,
                    'landsraad_bonus_active',
                    str(new_status).lower(),
                    'Whether the landsraad bonus is active (37.5 sand = 1 melange instead of 50)'
                )
                update_landsraad_bonus_status(new_status)
                conversion_rate = await get_sand_per_melange_with_bonus()
                action_text = "enabled" if new_status else "disabled"
                status_text = "🟢 **ACTIVE**" if new_status else "🔴 **INACTIVE**"
                rate_text = f"{conversion_rate} sand = 1 melange"
                fields = {
                    "📊 Status": status_text,
                    "⚙️ Conversion Rate": rate_text,
                    "💡 Effect": "37.5 sand = 1 melange" if new_status else "50 sand = 1 melange"
                }
                color = 0x00FF00 if new_status else 0xFF4500
                embed = build_status_embed(
                    title=f"🏛️ Landsraad Bonus {action_text.title()}",
                    description=f"Melange conversion rate updated to: **{rate_text}**",
                    color=color,
                    fields=fields,
                    timestamp=interaction.created_at
                )
                await self.send_response(interaction, embed=embed.build())
                log_command_metrics(
                    f"Landsraad {action.title()}", str(interaction.user.id), interaction.user.display_name, time.time() - command_start,
                    set_status_time=f"{set_status_time:.3f}s", new_status=new_status, conversion_rate=conversion_rate
                )

        except Exception as error:
            logger.error(f"Error in settings landsraad command: {error}",
                        user_id=str(interaction.user.id),
                        username=interaction.user.display_name,
                        action=action,
                        total_time=f"{time.time() - command_start:.3f}s")
            await self.send_response(interaction, f"❌ An error occurred while managing landsraad bonus: {error}", ephemeral=True)

    async def _handle_setting(
        self,
        interaction: discord.Interaction,
        value: Optional[Any],
        *,
        setting_key: str,
        db_description: str,
        get_func: Callable[[], Any],
        update_func: Callable[[Any], None],
        view_title: str,
        view_description_formatter: Callable[[Any], str],
        set_title: str,
        set_description_formatter: Callable[[Any], str],
        value_for_db: Callable[[Any], str],
        value_for_update: Callable[[Any], Any],
        log_name: str,
        set_embed_fields: Optional[Callable[[Any], Optional[Dict[str, str]]]] = None,
    ):
        """Generic handler for viewing or setting a global setting."""
        command_start = time.time()
        await interaction.response.defer(ephemeral=True)

        if not check_permission(interaction, 'admin_or_officer'):
            await self.send_response(interaction, "❌ You do not have permission to use this command.", ephemeral=True)
            return

        db = get_database()

        if value is None:
            # View logic
            current_value = get_func()
            description = view_description_formatter(current_value)
            embed = build_status_embed(title=view_title, description=description, color=0x3498DB)
            await self.send_response(interaction, embed=embed.build())
        else:
            # Set logic
            try:
                db_val = value_for_db(value)
                update_val = value_for_update(value)

                await db.set_global_setting(setting_key, db_val, db_description)
                update_func(update_val)

                description = set_description_formatter(value)
                fields = set_embed_fields(value) if set_embed_fields else None
                embed = build_status_embed(
                    title=set_title,
                    description=description,
                    color=0x00FF00,
                    fields=fields
                )
                await self.send_response(interaction, embed=embed.build())

                log_command_metrics(f"Settings {log_name}", str(interaction.user.id), interaction.user.display_name, time.time() - command_start, new_value=update_val)

            except Exception as e:
                logger.error(f"Error setting {setting_key}: {e}", user_id=str(interaction.user.id))
                await self.send_response(interaction, f"❌ An error occurred: {e}", ephemeral=True)

    @app_commands.command(name="user_cut", description="Set or view the default user cut percentage for /split.")
    @app_commands.describe(value="The default percentage for each user in a split (0 to unset).")
    async def user_cut(self, interaction: discord.Interaction, value: app_commands.Range[int, 0, 100] = None):
        """Set or view the default user cut for /split."""
        await self._handle_setting(
            interaction,
            value,
            setting_key='user_cut',
            db_description='Default user cut for /split command',
            get_func=get_user_cut,
            update_func=update_user_cut,
            view_title="⚙️ Default User Cut",
            view_description_formatter=lambda v: f"Current default user cut is **{v}%**." if v is not None else "Current default user cut is **Not set (optional in /split)**.",
            set_title="✅ Default User Cut Updated",
            set_description_formatter=lambda v: f"Default user cut has been set to **{'Unset' if v == 0 else f'{v}%'}**.",
            value_for_db=lambda v: str(v) if v != 0 else "",
            value_for_update=lambda v: v,
            log_name="UserCut"
        )

    @app_commands.command(name="guild_cut", description="Set or view the default guild cut percentage for /split.")
    @app_commands.describe(value="The default percentage for the guild in a split (0 for default 10%).")
    async def guild_cut(self, interaction: discord.Interaction, value: app_commands.Range[int, 0, 100] = None):
        """Set or view the default guild cut for /split."""
        await self._handle_setting(
            interaction,
            value,
            setting_key='guild_cut',
            db_description='Default guild cut for /split command',
            get_func=get_guild_cut,
            update_func=update_guild_cut,
            view_title="⚙️ Default Guild Cut",
            view_description_formatter=lambda v: f"Current default guild cut is **{v}%**.",
            set_title="✅ Default Guild Cut Updated",
            set_description_formatter=lambda v: f"Default guild cut has been set to **{v if v != 0 else 10}%**.",
            value_for_db=lambda v: str(v) if v != 0 else "",
            value_for_update=lambda v: v,
            log_name="GuildCut",
            set_embed_fields=lambda v: {"ℹ️ Note": "A value of 0 unsets the global default, reverting to the bot's default of 10%."} if v == 0 else None
        )

    @app_commands.command(name="region", description="Set or view the guild's primary region.")
    @app_commands.describe(region="The primary operational region.")
    @app_commands.choices(region=[
        app_commands.Choice(name="North America", value="na"),
        app_commands.Choice(name="Europe", value="eu"),
        app_commands.Choice(name="South America", value="sa"),
        app_commands.Choice(name="Asia", value="as"),
        app_commands.Choice(name="Oceania", value="oc"),
    ])
    async def region(self, interaction: discord.Interaction, region: app_commands.Choice[str] = None):
        """Set or view the guild's region."""
        region_map = {
            "na": "North America", "eu": "Europe", "sa": "South America",
            "as": "Asia", "oc": "Oceania"
        }
        await self._handle_setting(
            interaction,
            region,
            setting_key='region',
            db_description='Primary guild region',
            get_func=get_region,
            update_func=update_region,
            view_title="🌍 Guild Region",
            view_description_formatter=lambda v: f"Current guild region is **{region_map.get(v, 'Not set')}**.",
            set_title="✅ Guild Region Updated",
            set_description_formatter=lambda v: f"Guild region has been set to **{v.name}**.",
            value_for_db=lambda v: v.value,
            value_for_update=lambda v: v.value,
            log_name="Region"
        )