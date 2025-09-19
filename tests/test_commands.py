"""
Generic tests for bot commands using real database.
"""
import pytest
from unittest.mock import patch, Mock
from commands import COMMAND_METADATA


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

    @pytest.mark.asyncio
    async def test_split_command_with_user_cut(self, mock_interaction, test_database):
        """Test the split command with the new user_cut parameter."""
        from commands.split import split as split_command
        from unittest.mock import Mock, AsyncMock
        import discord
        import datetime

        # Configure the mock interaction
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

        # Patch get_database to use the test database
        with patch('commands.split.get_database', return_value=test_database):
            # Test case: split 1000 sand with 2 users, each getting a 20% cut
            await split_command(
                interaction=mock_interaction,
                total_sand=1000,
                users="<@123> <@456>",
                guild=10,
                user_cut=20,
                use_followup=True
            )

            # Verify that a response was sent via followup
            assert mock_interaction.followup.send.called, "Split command with user_cut did not send a followup response"


    @pytest.mark.asyncio
    async def test_split_command_with_conflicting_user_cut(self, mock_interaction, test_database):
        """Test the split command with a conflicting user_cut and individual percentages."""
        from commands.split import split as split_command

        # Patch get_database to use the test database
        with patch('commands.split.get_database', return_value=test_database):
            # Test case: split 1000 sand with a conflicting user_cut and individual percentages
            await split_command(
                interaction=mock_interaction,
                total_sand=1000,
                users="<@123> 30",
                guild=10,
                user_cut=20,
                use_followup=True
            )

            # Verify that an error message was sent
            assert mock_interaction.followup.send.called, "Split command with conflicting user_cut did not send a followup response"
            kwargs = mock_interaction.followup.send.call_args.kwargs
            assert "You cannot provide individual percentages when using `user_cut`" in kwargs['content']

def setup_split_mock_interaction(mock_interaction):
    """Helper function to set up the mock interaction for split command tests."""
    from unittest.mock import Mock, AsyncMock
    import discord
    import datetime

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
        """Test the split command with the new user_cut parameter."""
        from commands.split import split as split_command
        mock_interaction = setup_split_mock_interaction(mock_interaction)

        with patch('commands.split.get_database', return_value=test_database):
            await split_command(
                interaction=mock_interaction,
                total_sand=1000,
                users="<@123> <@456>",
                guild=10,
                user_cut=20,
                use_followup=True
            )

            assert mock_interaction.followup.send.called, "Split command with user_cut did not send a followup response"
            kwargs = mock_interaction.followup.send.call_args.kwargs
            embed = kwargs['embed']
            assert '4 melange' in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_split_command_with_invalid_user_cut(self, mock_interaction, test_database):
        """Test the split command with an invalid user_cut parameter."""
        from commands.split import split as split_command
        mock_interaction = setup_split_mock_interaction(mock_interaction)

        with patch('commands.split.get_database', return_value=test_database):
            await split_command(
                interaction=mock_interaction,
                total_sand=1000,
                users="<@123> <@456>",
                guild=10,
                user_cut=110,
                use_followup=True
            )

            assert mock_interaction.followup.send.called, "Split command with invalid user_cut did not send a followup response"
            kwargs = mock_interaction.followup.send.call_args.kwargs
            assert "User cut percentage must be between 0 and 100" in kwargs['content']

    @pytest.mark.asyncio
    async def test_split_command_with_conflicting_user_cut(self, mock_interaction, test_database):
        """Test the split command with a conflicting user_cut and individual percentages."""
        from commands.split import split as split_command
        mock_interaction = setup_split_mock_interaction(mock_interaction)

        with patch('commands.split.get_database', return_value=test_database):
            await split_command(
                interaction=mock_interaction,
                total_sand=1000,
                users="<@123> 30",
                guild=10,
                user_cut=20,
                use_followup=True
            )

            assert mock_interaction.followup.send.called, "Split command with conflicting user_cut did not send a followup response"
            kwargs = mock_interaction.followup.send.call_args.kwargs
            assert "You cannot provide individual percentages when using `user_cut`" in kwargs['content']

    @pytest.mark.asyncio
    async def test_split_command_with_user_cut_and_guild_warning(self, mock_interaction, test_database):
        """Test that a warning is shown when user_cut and a non-default guild cut are provided."""
        from commands.split import split as split_command
        import inspect
        mock_interaction = setup_split_mock_interaction(mock_interaction)

        # Get the default guild cut from the function signature
        sig = inspect.signature(split_command)
        default_guild_cut = sig.parameters['guild'].default
        non_default_guild_cut = default_guild_cut + 10

        with patch('commands.split.get_database', return_value=test_database):
            await split_command(
                interaction=mock_interaction,
                total_sand=1000,
                users="<@123> <@456>",
                guild=non_default_guild_cut,
                user_cut=20,
                use_followup=True
            )

            assert mock_interaction.followup.send.called, "Split command with user_cut and guild cut did not send a followup response"
            # The first call should be the warning
            first_call_kwargs = mock_interaction.followup.send.call_args_list[0].kwargs
            total_percentage = 20 * 2
            expected_warning = f"User percentages ({total_percentage}%) and the specified guild cut ({non_default_guild_cut}%) do not sum to 100%"
            assert expected_warning in first_call_kwargs.get('content', '')

    @pytest.mark.asyncio
    async def test_commands_with_invalid_inputs(self, mock_interaction, test_database):
        """Test that commands handle invalid inputs gracefully."""
        # Test edge cases for commands that take parameters
        edge_cases = [
            ('sand', 'sand', [0, True], {}),  # Too low
            ('sand', 'sand', [15000, True], {}),  # Too high
            ('reset', 'reset', [False, True], {}),  # Not confirmed
        ]

        for module_name, function_name, args, kwargs in edge_cases:
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
            'help': 'help',
            'reset': 'reset',
            'ledger': 'ledger',
            'expedition': 'expedition',
            'pay': 'pay',
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
