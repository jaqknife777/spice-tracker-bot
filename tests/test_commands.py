"""
Generic tests for bot commands.
"""
import pytest
from unittest.mock import patch, Mock
from commands import COMMAND_METADATA


class TestCommandResponsiveness:
    """Test that all commands respond appropriately."""

    @pytest.mark.asyncio
    async def test_all_commands_respond(self, mock_interaction, mock_database):
        """Test that all commands can execute and respond without crashing."""
        # Map of module names to actual function names and parameters
        test_cases = [
            ('sand', 'sand', [100, True], {}),
            ('refinery', 'refinery', [True], {}),
            ('leaderboard', 'leaderboard', [10, True], {}),

            ('split', 'split', [1000, '@user1 @user2', True], {}),
            ('fixedratecut', 'fixedratecut', [10000, '<@12345>', 5, True], {}),
            ('help', 'help', [True], {}),
            ('reset', 'reset', [True, True], {}),
            ('ledger', 'ledger', [True], {}),
            ('expedition', 'expedition', [1, True], {}),
            ('payment', 'pay', [Mock(id=123, display_name="TestUser"), None, True], {}),
            ('payroll', 'payroll', [True], {}),
        ]

        for module_name, function_name, args, kwargs in test_cases:
            try:
                # Get the command function
                command_func = getattr(__import__(f'commands.{module_name}', fromlist=[module_name]), function_name)

                # Mock the database for this command - try different import paths
                try:
                    with patch(f'commands.{module_name}.get_database', return_value=mock_database):
                        await command_func(mock_interaction, *args, **kwargs)
                except AttributeError:
                    # Try patching utils.helpers.get_database instead
                    with patch('utils.helpers.get_database', return_value=mock_database):
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

    @pytest.mark.asyncio
    async def test_commands_with_invalid_inputs(self, mock_interaction, mock_database):
        """Test that commands handle invalid inputs gracefully."""
        # Test edge cases for commands that take parameters
        edge_cases = [
            ('sand', 'sand', [0, True], {}),  # Too low
            ('sand', 'sand', [15000, True], {}),  # Too high
            ('split', 'split', [0, '@user1', True], {}),  # Invalid sand amount
            ('split', 'split', [1000, '@user1', True], {}),  # Valid split
            ('fixedratecut', 'fixedratecut', [0, '@user1', 5, True], {}),
            ('fixedratecut', 'fixedratecut', [1000, '@user1', -1, True], {}),
            ('fixedratecut', 'fixedratecut', [1000, '@user1', 101, True], {}),
            ('fixedratecut', 'fixedratecut', [1000, '', 5, True], {}),
            ('fixedratecut', 'fixedratecut', [1000, '<@1> <@2> <@3> <@4> <@5> <@6> <@7> <@8> <@9> <@10> <@11> <@12> <@13> <@14> <@15> <@16> <@17> <@18> <@19> <@20> <@21>', 5, True], {}),
            ('reset', 'reset', [False, True], {}),  # Not confirmed
        ]

        for module_name, function_name, args, kwargs in edge_cases:
            try:
                # Get the command function
                command_func = getattr(__import__(f'commands.{module_name}', fromlist=[module_name]), function_name)

                # Mock the database for this command - try different import paths
                try:
                    with patch(f'commands.{module_name}.get_database', return_value=mock_database):
                        await command_func(mock_interaction, *args, **kwargs)
                except AttributeError:
                    # Try patching utils.helpers.get_database instead
                    with patch('utils.helpers.get_database', return_value=mock_database):
                        await command_func(mock_interaction, *args, **kwargs)

                # Verify some form of response was sent
                response_sent = (
                    mock_interaction.followup.send.called or
                    mock_interaction.response.send.called or
                    mock_interaction.channel.send.called or
                    mock_interaction.response.send_modal.called
                )

                assert response_sent, f"Command {function_name} did not send any response to invalid input"

                # Reset mocks for next test
                mock_interaction.followup.send.reset_mock()
                mock_interaction.response.send.reset_mock()
                mock_interaction.channel.send.reset_mock()
                mock_interaction.response.send_modal.reset_mock()

            except Exception as e:
                pytest.fail(f"Command {function_name} failed with error on invalid input: {e}")

    @pytest.mark.asyncio
    async def test_landsraad_bonus_sand_command(self, mock_interaction, mock_database):
        """Test the sand command with the landsraad_bonus flag."""
        from commands.sand import sand
        with patch('commands.sand.get_sand_per_melange') as mock_get_sand_per_melange, \
             patch('commands.sand.get_database', return_value=mock_database), \
             patch('commands.sand.is_officer', return_value=True):

            mock_get_sand_per_melange.return_value = 37
            await sand(mock_interaction, 100, landsraad_bonus=True)
            mock_get_sand_per_melange.assert_called_with(landsraad_bonus=True)

    @pytest.mark.asyncio
    async def test_landsraad_bonus_split_command(self, mock_interaction, mock_database):
        """Test the split command with the landsraad_bonus flag."""
        from commands.split import split
        with patch('commands.split.get_sand_per_melange') as mock_get_sand_per_melange, \
             patch('commands.split.get_database', return_value=mock_database), \
             patch('commands.split.is_officer', return_value=True):

            mock_get_sand_per_melange.return_value = 37
            await split(mock_interaction, 1000, '<@12345>', 10, landsraad_bonus=True)
            mock_get_sand_per_melange.assert_called_with(landsraad_bonus=True)

    @pytest.mark.asyncio
    async def test_landsraad_bonus_fixedratecut_command(self, mock_interaction, mock_database):
        """Test the fixedratecut command with the landsraad_bonus flag."""
        from commands.fixedratecut import fixedratecut
        with patch('commands.fixedratecut.get_sand_per_melange') as mock_get_sand_per_melange, \
             patch('commands.fixedratecut.get_database', return_value=mock_database), \
             patch('commands.fixedratecut.is_officer', return_value=True):

            mock_get_sand_per_melange.return_value = 37
            await fixedratecut(mock_interaction, 10000, '<@12345>', 5, landsraad_bonus=True)
            mock_get_sand_per_melange.assert_called_with(landsraad_bonus=True)

    def test_command_metadata_structure(self):
        """Test that all commands have proper metadata structure."""
        for command_name, metadata in COMMAND_METADATA.items():
            # Check required metadata fields
            assert 'description' in metadata, f"Command {command_name} missing description"
            assert isinstance(metadata['description'], str), f"Command {command_name} description must be string"

            # Check optional fields if present
            if 'aliases' in metadata:
                assert isinstance(metadata['aliases'], list), f"Command {command_name} aliases must be list"

            if 'params' in metadata:
                assert isinstance(metadata['params'], dict), f"Command {command_name} params must be dict"

    def test_command_functions_exist(self):
        """Test that all command functions can be imported and are callable."""
        # Map of module names to actual function names
        function_name_map = {
            'sand': 'sand',
            'refinery': 'refinery',
            'leaderboard': 'leaderboard',
            'split': 'split',
            'fixedratecut': 'fixedratecut',
            'help': 'help',
            'reset': 'reset',
            'ledger': 'ledger',
            'expedition': 'expedition',
            'payment': 'pay',
            'payroll': 'payroll',
        }

        for command_name in COMMAND_METADATA.keys():
            try:
                # Import the command module
                command_module = __import__(f'commands.{command_name}', fromlist=[command_name])

                # Get the actual function name for this command
                actual_function_name = function_name_map.get(command_name, command_name)

                # Get the command function
                command_func = getattr(command_module, actual_function_name, None)

                assert command_func is not None, f"Command function {actual_function_name} not found in {command_name}"
                assert callable(command_func), f"Command function {actual_function_name} is not callable"

            except ImportError as e:
                pytest.fail(f"Could not import command {command_name}: {e}")
            except AttributeError as e:
                pytest.fail(f"Command function {actual_function_name} not found in module {command_name}: {e}")
