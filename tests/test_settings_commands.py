import pytest
from unittest.mock import patch, Mock
from commands.settings import Settings
from utils.helpers import (
    get_user_cut, get_guild_cut, get_region, update_user_cut, update_guild_cut, update_region,
    get_admin_roles, get_officer_roles, get_user_roles,
    update_admin_roles, update_officer_roles, update_user_roles
)

@pytest.fixture(autouse=True)
def mock_get_db(mocker, test_database):
    mocker.patch('commands.settings.get_database', return_value=test_database, create=True)
    # Reset cached roles before each test
    update_admin_roles([])
    update_officer_roles([])
    update_user_roles([])

class TestSettingsCommand:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("role_type, command_name, get_func, permission_level", [
        ("admin", "admin_roles", get_admin_roles, "admin"),
        ("officer", "officer_roles", get_officer_roles, "admin_or_officer"),
        ("user", "user_roles", get_user_roles, "admin_or_officer"),
    ])
    async def test_settings_role_commands(self, mock_interaction, role_type, command_name, get_func, permission_level):
        settings_command_group = Settings(bot=None)
        command = getattr(settings_command_group, command_name)

        with patch('commands.settings.check_permission') as mock_check_permission:
            # Test permission denied
            mock_check_permission.return_value = False
            mock_interaction.response.is_done = Mock(return_value=False)
            await command.callback(settings_command_group, mock_interaction, roles="123")
            mock_interaction.response.send_message.assert_called_with("❌ You do not have permission to use this command.", ephemeral=True)
            mock_interaction.reset_mock()

            # Test view when no roles are set
            mock_check_permission.return_value = True
            mock_interaction.response.is_done = Mock(return_value=True)
            await command.callback(settings_command_group, mock_interaction, roles=None)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "Currently configured roles: None" in embed.description
            assert get_func() == []
            mock_interaction.reset_mock()

            # Test setting roles with IDs
            await command.callback(settings_command_group, mock_interaction, roles="12345, 67890")
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "Roles updated to: <@&12345>, <@&67890>" in embed.description
            assert get_func() == [12345, 67890]
            mock_interaction.reset_mock()

            # Test setting roles with mentions
            await command.callback(settings_command_group, mock_interaction, roles="<@&98765> <@&43210>")
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "Roles updated to: <@&43210>, <@&98765>" in embed.description
            assert get_func() == [43210, 98765]
            mock_interaction.reset_mock()

            # Test setting roles with mixed input and duplicates
            await command.callback(settings_command_group, mock_interaction, roles="<@&11111>, 22222 <@&11111>")
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "Roles updated to: <@&11111>, <@&22222>" in embed.description
            assert get_func() == [11111, 22222]
            mock_interaction.reset_mock()

            # Test viewing the set roles
            await command.callback(settings_command_group, mock_interaction, roles=None)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "Currently configured roles: <@&11111>, <@&22222>" in embed.description
            mock_interaction.reset_mock()

            # Test clearing roles
            await command.callback(settings_command_group, mock_interaction, roles="")
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "Roles updated to: None" in embed.description
            assert get_func() == []

    @pytest.mark.asyncio
    async def test_settings_user_cut(self, mock_interaction):
        settings_command_group = Settings(bot=None)
        with patch('commands.settings.check_permission', return_value=True):
            update_user_cut(None)
            mock_interaction.response.is_done = Mock(return_value=True)
            await settings_command_group.user_cut.callback(settings_command_group, mock_interaction, value=None)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "Not set" in embed.description
            mock_interaction.reset_mock()

            mock_interaction.response.is_done = Mock(return_value=True)
            await settings_command_group.user_cut.callback(settings_command_group, mock_interaction, value=15)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "set to **15%**" in embed.description
            assert get_user_cut() == 15
            mock_interaction.reset_mock()

            mock_interaction.response.is_done = Mock(return_value=True)
            await settings_command_group.user_cut.callback(settings_command_group, mock_interaction, value=0)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "set to **Unset**" in embed.description
            assert get_user_cut() is None

    @pytest.mark.asyncio
    async def test_settings_guild_cut(self, mock_interaction):
        settings_command_group = Settings(bot=None)
        with patch('commands.settings.check_permission', return_value=True):
            update_guild_cut(None)
            mock_interaction.response.is_done = Mock(return_value=True)
            await settings_command_group.guild_cut.callback(settings_command_group, mock_interaction, value=None)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "is **10%**" in embed.description
            mock_interaction.reset_mock()

            mock_interaction.response.is_done = Mock(return_value=True)
            await settings_command_group.guild_cut.callback(settings_command_group, mock_interaction, value=25)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "set to **25%**" in embed.description
            assert get_guild_cut() == 25
            mock_interaction.reset_mock()

            mock_interaction.response.is_done = Mock(return_value=True)
            await settings_command_group.guild_cut.callback(settings_command_group, mock_interaction, value=0)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "set to **10%**" in embed.description
            assert get_guild_cut() == 10

    @pytest.mark.asyncio
    async def test_settings_region(self, mock_interaction):
        settings_command_group = Settings(bot=None)
        with patch('commands.settings.check_permission', return_value=True):
            update_region(None)
            mock_interaction.response.is_done = Mock(return_value=True)
            await settings_command_group.region.callback(settings_command_group, mock_interaction, region=None)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "is **Not set**" in embed.description
            mock_interaction.reset_mock()

            mock_choice = Mock()
            mock_choice.name = "Europe"
            mock_choice.value = "eu"
            mock_interaction.response.is_done = Mock(return_value=True)
            await settings_command_group.region.callback(settings_command_group, mock_interaction, region=mock_choice)
            embed = mock_interaction.followup.send.call_args.kwargs['embed']
            assert "set to **Europe**" in embed.description
            assert get_region() == "eu"