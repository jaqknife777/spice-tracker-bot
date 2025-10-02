import pytest
from unittest.mock import Mock, patch
from utils.permissions import is_admin, is_officer, is_user, check_permission, _get_command_permission_level
from utils.helpers import update_admin_roles, update_officer_roles, update_user_roles

@pytest.fixture(autouse=True)
def reset_roles():
    """Reset all cached roles before each test."""
    update_admin_roles([])
    update_officer_roles([])
    update_user_roles([])

@pytest.fixture
def mock_interaction():
    """Creates a mock interaction object with a user that has roles."""
    interaction = Mock()
    interaction.user = Mock()
    return interaction

def set_user_roles(interaction, role_ids):
    """Helper to set roles on the mock user."""
    interaction.user.roles = [Mock(id=rid) for rid in role_ids]

class TestPermissions:
    @pytest.mark.asyncio
    async def test_is_admin(self, mock_interaction):
        update_admin_roles([101, 102])
        set_user_roles(mock_interaction, [101, 201])
        assert is_admin(mock_interaction) is True

        set_user_roles(mock_interaction, [201, 202])
        assert is_admin(mock_interaction) is False

        update_admin_roles([])
        set_user_roles(mock_interaction, [101, 201])
        assert is_admin(mock_interaction) is False

    @pytest.mark.asyncio
    async def test_is_admin_bot_owner(self, mock_interaction, mocker):
        # Patch os.getenv in the permissions module to simulate BOT_OWNER_ID
        mocker.patch('utils.permissions.os.getenv', return_value='987654321')

        # Set the interaction user to be the bot owner
        mock_interaction.user.id = 987654321
        set_user_roles(mock_interaction, [111])  # A non-admin role

        # The bot owner should always be an admin, regardless of roles
        assert is_admin(mock_interaction) is True

        # Now test a regular user who is not the owner
        mock_interaction.user.id = 123456789
        update_admin_roles([101])
        set_user_roles(mock_interaction, [111])  # Not an admin role
        assert is_admin(mock_interaction) is False  # Not owner, no role -> False

        set_user_roles(mock_interaction, [101])  # Has admin role
        assert is_admin(mock_interaction) is True  # Not owner, has role -> True

    @pytest.mark.asyncio
    async def test_is_officer(self, mock_interaction):
        update_officer_roles([201, 202])
        set_user_roles(mock_interaction, [101, 201])
        assert is_officer(mock_interaction) is True

        set_user_roles(mock_interaction, [101, 102])
        assert is_officer(mock_interaction) is False

        update_officer_roles([])
        set_user_roles(mock_interaction, [201, 301])
        assert is_officer(mock_interaction) is False

    @pytest.mark.asyncio
    async def test_is_user(self, mock_interaction):
        update_user_roles([301, 302])
        set_user_roles(mock_interaction, [101, 301])
        assert is_user(mock_interaction) is True

        set_user_roles(mock_interaction, [101, 201])
        assert is_user(mock_interaction) is False

        # If no user roles are configured, everyone is a user
        update_user_roles([])
        set_user_roles(mock_interaction, [401, 402])
        assert is_user(mock_interaction) is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("permission_level, expected", [
        ("admin", True),
        ("officer", False), # An admin is not implicitly an officer
        ("admin_or_officer", True),
        ("user", True),
        ("any", True),
    ])
    async def test_check_permission_as_admin(self, mock_interaction, permission_level, expected):
        update_admin_roles([101])
        set_user_roles(mock_interaction, [101])
        assert check_permission(mock_interaction, permission_level) is expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize("permission_level, expected", [
        ("admin", False),
        ("officer", True),
        ("admin_or_officer", True),
        ("user", True),
        ("any", True),
    ])
    async def test_check_permission_as_officer(self, mock_interaction, permission_level, expected):
        update_officer_roles([201])
        set_user_roles(mock_interaction, [201])
        assert check_permission(mock_interaction, permission_level) is expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize("permission_level, expected", [
        ("admin", False),
        ("officer", False),
        ("admin_or_officer", False),
        ("user", True),
        ("any", True),
    ])
    async def test_check_permission_as_user(self, mock_interaction, permission_level, expected):
        update_user_roles([301])
        set_user_roles(mock_interaction, [301])
        assert check_permission(mock_interaction, permission_level) is expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize("permission_level, expected", [
        ("admin", False),
        ("officer", False),
        ("admin_or_officer", False),
        ("user", False),
        ("any", True),
    ])
    async def test_check_permission_as_unauthorized(self, mock_interaction, permission_level, expected):
        update_admin_roles([101])
        update_officer_roles([201])
        update_user_roles([301])
        set_user_roles(mock_interaction, [401]) # User has no configured roles
        assert check_permission(mock_interaction, permission_level) is expected

    @pytest.mark.asyncio
    async def test_check_permission_as_unauthorized_when_all_users_allowed(self, mock_interaction):
        # If user_roles is empty, all users should have 'user' permission
        update_user_roles([])
        set_user_roles(mock_interaction, [401])
        assert check_permission(mock_interaction, "user") is True

class TestCommandPermissionMapping:
    @pytest.mark.parametrize("command_name, expected_level", [
        # Admin commands
        ("reset", "admin"),
        ("pay", "admin"),
        # User commands
        ("sand", "user"),
        ("split", "user"),
        ("leaderboard", "user"),
        # Any commands
        ("help", "any"),
        ("perms", "any"),
        ("calc", "any"),
        # Default case
        ("some_unknown_command", "user"),
    ])
    def test_get_command_permission_level(self, command_name, expected_level):
        """Tests the mapping of command names to permission levels."""
        assert _get_command_permission_level(command_name) == expected_level