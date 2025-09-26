"""
Tests for bot commands.
"""
import pytest
from unittest.mock import patch, Mock
from commands.settings import Settings
from commands.split import split
from utils.helpers import get_user_cut, get_guild_cut, get_region, update_user_cut, update_guild_cut, update_region
import datetime

def setup_split_mock_interaction(mock_interaction):
    """Helper function to set up the mock interaction for split command tests."""
    from unittest.mock import Mock, AsyncMock
    import discord

    mock_interaction.created_at = datetime.datetime.now(datetime.timezone.utc)
    async def mock_fetch_member(user_id):
        mock_user = Mock(spec=discord.Member)
        mock_user.id = int(user_id)
        mock_user.display_name = f"TestUser{user_id}"
        mock_user.mention = f"<@{user_id}>"
        return mock_user

    mock_interaction.guild.fetch_member = AsyncMock(side_effect=mock_fetch_member)
    mock_interaction.client.fetch_user = AsyncMock(side_effect=mock_fetch_member)
    mock_interaction.response.is_done.return_value = True
    return mock_interaction

class TestSplitCommand:
    @pytest.mark.asyncio
    async def test_split_command_with_user_cut(self, mock_interaction, test_database):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        with patch('commands.split.get_database', return_value=test_database), \
             patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> <@456>", guild=10, user_cut=20)
            assert mock_send_response.call_count == 2
            final_call_kwargs = mock_send_response.call_args.kwargs
            embed = final_call_kwargs['embed']
            assert '4 melange' in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_split_command_with_invalid_user_cut(self, mock_interaction, test_database):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        with patch('commands.split.get_database', return_value=test_database), \
             patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> <@456>", guild=10, user_cut=110)
            mock_send_response.assert_called_once()
            content_arg = mock_send_response.call_args.args[1]
            assert "User cut percentage must be between 0 and 100" in content_arg

    @pytest.mark.asyncio
    async def test_split_command_with_conflicting_user_cut(self, mock_interaction, test_database):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        with patch('commands.split.get_database', return_value=test_database), \
             patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> 30", guild=10, user_cut=20)
            mock_send_response.assert_called_once()
            content_arg = mock_send_response.call_args.args[1]
            assert "You cannot provide individual percentages when using `user_cut`" in content_arg

    @pytest.mark.asyncio
    async def test_split_command_with_user_cut_and_guild_warning(self, mock_interaction, test_database):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        default_guild_cut = get_guild_cut()
        non_default_guild_cut = default_guild_cut + 10
        with patch('commands.split.get_database', return_value=test_database), \
             patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> <@456>", guild=non_default_guild_cut, user_cut=20)
            assert mock_send_response.called
            first_call_args = mock_send_response.call_args_list[0].args
            content_arg = first_call_args[1]
            total_percentage = 20 * 2
            expected_warning = f"User percentages ({total_percentage}%) and the specified guild cut ({non_default_guild_cut}%) do not sum to 100%"
            assert expected_warning in content_arg

    @pytest.mark.asyncio
    async def test_split_command_uses_global_defaults(self, mock_interaction, test_database):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        update_guild_cut(20)
        update_user_cut(15)
        with patch('commands.split.get_database', return_value=test_database), \
             patch('commands.split.get_sand_per_melange_with_bonus', return_value=50.0), \
             patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> <@456>", guild=None, user_cut=None)
            assert mock_send_response.call_count == 2
            final_call_kwargs = mock_send_response.call_args.kwargs
            embed = final_call_kwargs['embed']
            assert '**TestUser123**: 3 melange (15.0%)' in embed.fields[0].value
            assert '**TestUser456**: 3 melange (15.0%)' in embed.fields[0].value
            assert '70.0%' in embed.fields[1].value
            assert '14 melange' in embed.fields[1].value
        update_guild_cut(None)
        update_user_cut(None)

class TestCommandResponsiveness:
    """Test that all commands respond appropriately with real database."""

    @pytest.mark.asyncio
    async def test_all_commands_respond(self, mock_interaction, test_database):
        """Test that all commands can execute and respond without crashing."""
        # Map of module names to actual function names and parameters
        test_cases = [
            ('sand', 'sand', [100, True], {}),
            ('refinery', 'refinery', [True], {}),
            ('leaderboard', 'leaderboard', [10, True], {}),
            ('help', 'help', [True], {}),
            ('reset', 'reset', [True, True], {}),
            ('ledger', 'ledger', [True], {}),
            ('expedition', 'expedition', [1, True], {}),
            ('pay', 'pay', [Mock(id=123, display_name="TestUser"), None, True], {}),
            ('payroll', 'payroll', [True], {}),
        ]

        for module_name, function_name, args, kwargs in test_cases:
            try:
                # Get the command function
                command_func = getattr(__import__(f'commands.{module_name}', fromlist=[module_name]), function_name)

                # Use real database - try different import paths
                try:
                    with patch(f'commands.{module_name}.get_database', return_value=test_database):
                        await command_func(mock_interaction, *args, **kwargs)
                except AttributeError:
                    # Try patching utils.helpers.get_database instead
                    with patch('utils.helpers.get_database', return_value=test_database):
                        await command_func(mock_interaction, *args, **kwargs)

                # Verify some form of response was sent (either followup.send or response.send)
                response_sent = (
                    mock_interaction.followup.send.called or
                    mock_interaction.response.send.called or
                    mock_interaction.channel.send.called or
                    mock_interaction.response.send_modal.called
                )

                assert response_sent, f"Command {function_name} did not send any response"

                # Reset mocks for next test
                mock_interaction.followup.send.reset_mock()
                mock_interaction.response.send.reset_mock()
                mock_interaction.channel.send.reset_mock()
                mock_interaction.response.send_modal.reset_mock()

            except Exception as e:
                pytest.fail(f"Command {function_name} failed with error: {e}")

class TestSettingsCommand:
    @pytest.mark.asyncio
    async def test_settings_user_cut(self, mock_interaction, test_database):
        settings_command_group = Settings(bot=None)
        with patch('commands.settings.check_permission', return_value=True), \
             patch('commands.settings.get_database', return_value=test_database):
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
    async def test_settings_guild_cut(self, mock_interaction, test_database):
        settings_command_group = Settings(bot=None)
        with patch('commands.settings.check_permission', return_value=True), \
             patch('commands.settings.get_database', return_value=test_database):
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
    async def test_settings_region(self, mock_interaction, test_database):
        settings_command_group = Settings(bot=None)
        with patch('commands.settings.check_permission', return_value=True), \
             patch('commands.settings.get_database', return_value=test_database):
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