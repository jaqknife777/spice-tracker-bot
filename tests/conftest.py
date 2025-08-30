"""
Pytest configuration and common fixtures for the Spice Tracker Bot tests.
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

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
    return interaction

@pytest.fixture
def mock_database():
    """Create a mock database for testing."""
    db = Mock()
    db.initialize = AsyncMock()
    db.upsert_user = AsyncMock()
    db.add_deposit = AsyncMock()
    db.get_user_deposits = AsyncMock(return_value=[])
    db.get_user_stats = AsyncMock(return_value={
        'total_sand': 1000,
        'paid_sand': 500,
        'total_melange': 20,
        'timing': {'add_deposit_time': 0.1}
    })
    db.update_user_melange = AsyncMock()
    db.create_expedition = AsyncMock(return_value=1)
    db.add_expedition_participant = AsyncMock()
    db.add_expedition_deposit = AsyncMock()
    db.get_expedition_participants = AsyncMock(return_value=[])
    db.cleanup_old_deposits = AsyncMock(return_value=0)
    return db

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
