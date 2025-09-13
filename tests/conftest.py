"""
Pytest configuration and common fixtures for the Spice Tracker Bot tests.
"""
import pytest
import pytest_asyncio
import asyncio
import os
import tempfile
from unittest.mock import Mock, AsyncMock
from dotenv import load_dotenv
from database_orm import Database

# Load environment variables for testing
load_dotenv()

# Set testing environment
os.environ['TESTING'] = 'true'

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction for testing."""
    interaction = Mock()
    interaction.user.id = 123456789
    interaction.user.display_name = "TestUser"
    interaction.user.name = "testuser"
    interaction.created_at = Mock()
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.guild = Mock()
    interaction.guild.id = 987654321
    interaction.guild.name = "TestGuild"
    interaction.channel = Mock()

    # Make response methods properly async
    interaction.response.send = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()

    # Make channel methods async for fallback responses
    interaction.channel.send = AsyncMock()

    return interaction

@pytest_asyncio.fixture
async def test_database():
    """Create a real SQLite database for testing using SQLAlchemy ORM with Alembic migrations."""
    # Create a temporary database file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    # Set DATABASE_URL to SQLite for testing
    original_url = os.environ.get('DATABASE_URL')
    os.environ['DATABASE_URL'] = f'sqlite+aiosqlite:///{temp_file.name}'

    try:
        # Run migrations to set up the database schema
        import subprocess
        result = subprocess.run(['python', 'migrate.py', 'apply'],
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode != 0:
            print(f"Migration failed: {result.stderr}")
            # Fallback to direct initialization if migrations fail
            db = Database()
            await db.initialize()
        else:
            # Create database instance (migrations already applied)
            db = Database()
            await db.initialize()

        yield db

        # Cleanup: close database and remove temp file
        try:
            await db.reset_all_stats()  # Clear all data
        except Exception:
            pass  # Ignore cleanup errors

    finally:
        # Restore original DATABASE_URL
        if original_url:
            os.environ['DATABASE_URL'] = original_url
        elif 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

        # Remove the temporary file
        try:
            os.unlink(temp_file.name)
        except Exception:
            pass  # Ignore file removal errors

# Mock database fixture removed - using real database for all tests

@pytest.fixture
def mock_bot_instance():
    """Create a mock bot instance for testing."""
    bot = Mock()
    bot.tree = Mock()
    bot.tree.command = Mock()
    bot.guilds = [Mock()]
    bot.guilds[0].id = 987654321
    bot.guilds[0].name = "TestGuild"
    return bot

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'user_id': '123456789',
        'username': 'TestUser',
        'total_sand': 1000,
        'paid_sand': 500,
        'total_melange': 20
    }

@pytest.fixture
def sample_expedition_data():
    """Sample expedition data for testing."""
    return {
        'expedition_id': 1,
        'total_sand': 5000,
        'harvester_percentage': 10.0,
        'sand_per_melange': 50
    }
