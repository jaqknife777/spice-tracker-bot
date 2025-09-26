import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, AsyncMock

from database_orm import Database, Base
from sqlalchemy.ext.asyncio import create_async_engine

# This fixture will be used by all tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def test_database():
    """Fixture to set up and tear down the in-memory database for each test."""
    db_url = "sqlite+aiosqlite:///:memory:"
    database = Database(database_url=db_url, for_testing=True)

    # Create tables before each test
    await database.initialize()

    yield database

    # Drop all tables after each test
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def mock_interaction():
    """Fixture to create a mock interaction object."""
    interaction = MagicMock()
    interaction.user.id = "123456789"
    interaction.user.display_name = "TestUser"
    interaction.guild.id = "987654321"
    interaction.guild.name = "Test Guild"

    # Mock the response and followup attributes with AsyncMock for awaitable methods
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)

    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()

    interaction.channel = MagicMock()
    interaction.channel.send = AsyncMock()

    return interaction