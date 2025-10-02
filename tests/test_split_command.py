import pytest
from unittest.mock import patch, Mock, AsyncMock
from commands.split import split
from utils.helpers import get_user_cut, get_guild_cut, update_user_cut, update_guild_cut
import datetime
import discord

@pytest.fixture(autouse=True)
def mock_get_db(mocker, test_database):
    mocker.patch('commands.split.get_database', return_value=test_database, create=True)

def setup_split_mock_interaction(mock_interaction):
    """Helper function to set up the mock interaction for split command tests."""
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
    async def test_split_command_with_user_cut(self, mock_interaction):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        with patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> <@456>", guild=10, user_cut=20)
            assert mock_send_response.call_count == 2
            final_call_kwargs = mock_send_response.call_args.kwargs
            embed = final_call_kwargs['embed']
            assert '4 melange' in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_split_command_with_invalid_user_cut(self, mock_interaction):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        with patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> <@456>", guild=10, user_cut=110)
            mock_send_response.assert_called_once()
            content_arg = mock_send_response.call_args.args[1]
            assert "User cut percentage must be between 0 and 100" in content_arg

    @pytest.mark.asyncio
    async def test_split_command_with_conflicting_user_cut(self, mock_interaction):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        with patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> 30", guild=10, user_cut=20)
            mock_send_response.assert_called_once()
            content_arg = mock_send_response.call_args.args[1]
            assert "You cannot provide individual percentages when using `user_cut`" in content_arg

    @pytest.mark.asyncio
    async def test_split_command_with_user_cut_and_guild_warning(self, mock_interaction):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        default_guild_cut = get_guild_cut()
        non_default_guild_cut = default_guild_cut + 10
        with patch('commands.split.send_response') as mock_send_response:
            await split(mock_interaction, total_sand=1000, users="<@123> <@456>", guild=non_default_guild_cut, user_cut=20)
            assert mock_send_response.called
            first_call_args = mock_send_response.call_args_list[0].args
            content_arg = first_call_args[1]
            total_percentage = 20 * 2
            expected_warning = f"User percentages ({total_percentage}%) and the specified guild cut ({non_default_guild_cut}%) do not sum to 100%"
            assert expected_warning in content_arg

    @pytest.mark.asyncio
    async def test_split_command_uses_global_defaults(self, mock_interaction):
        mock_interaction = setup_split_mock_interaction(mock_interaction)
        update_guild_cut(20)
        update_user_cut(15)
        with patch('commands.split.get_sand_per_melange_with_bonus', return_value=50.0), \
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