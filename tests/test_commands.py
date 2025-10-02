import pytest
import time
from unittest.mock import patch, Mock, AsyncMock

@pytest.fixture(autouse=True)
def mock_get_db(mocker, test_database):
    """Fixture to automatically mock get_database in all command modules."""
    mocker.patch('utils.helpers.get_database', return_value=test_database)
    # Also patch it where it's directly imported in modules
    for module in ['sand', 'refinery', 'leaderboard', 'ledger', 'expedition', 'pay']:
        mocker.patch(f'commands.{module}.get_database', return_value=test_database, create=True)

@pytest.mark.parametrize(
    "command_module, command_name, args",
    [
        ("sand", "sand", (100, True)),
        ("refinery", "refinery", (True,)),
        ("leaderboard", "leaderboard", (10, True)),
        ("help", "help", (True,)),
        ("ledger", "ledger", (True,)),
        ("expedition", "expedition", (1, True)),
        ("pay", "pay", (Mock(id=123, display_name="TestUser"), None, True)),
    ]
)
@pytest.mark.asyncio
async def test_command_responds(mock_interaction, command_module, command_name, args):
    """Smoke test to ensure basic commands respond without errors."""
    module = __import__(f"commands.{command_module}", fromlist=[command_name])
    command_func = getattr(module, command_name)

    # Use a generic send_response patch since we don't know the exact module
    with patch(f'commands.{command_module}.send_response', new_callable=AsyncMock) as mock_send:
        try:
            # Call the wrapped function if it exists, otherwise the raw function
            if hasattr(command_func, '__wrapped__'):
                await command_func.__wrapped__(mock_interaction, time.time(), *args)
            else:
                await command_func(mock_interaction, *args)
        except Exception as e:
            pytest.fail(f"Command '{command_name}' raised an exception: {e}")

    mock_send.assert_called_once()