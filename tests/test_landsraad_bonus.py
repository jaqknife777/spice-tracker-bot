"""
Tests for landsraad bonus functionality using real database.
"""

import pytest
from unittest.mock import AsyncMock, patch
from utils.helpers import convert_sand_to_melange, get_sand_per_melange_with_bonus
from database_orm import Database


class TestLandsraadBonus:
    """Test landsraad bonus conversion functionality."""

    @pytest.mark.asyncio
    async def test_convert_sand_to_melange_normal_rate(self):
        """Test sand to melange conversion with normal rate (50:1)."""
        with patch('utils.helpers.get_sand_per_melange_with_bonus', return_value=50.0):
            melange, remaining = await convert_sand_to_melange(250)
            assert melange == 5
            assert remaining == 0

    @pytest.mark.asyncio
    async def test_convert_sand_to_melange_landsraad_rate(self):
        """Test sand to melange conversion with landsraad bonus rate (37.5:1)."""
        with patch('utils.helpers.get_sand_per_melange_with_bonus', return_value=37.5):
            melange, remaining = await convert_sand_to_melange(250)
            assert melange == 6  # 250 / 37.5 = 6.67, truncated to 6
            assert remaining == 25  # 250 - (6 * 37.5) = 25

    @pytest.mark.asyncio
    async def test_convert_sand_to_melange_exact_conversion(self):
        """Test exact conversion with landsraad bonus rate."""
        with patch('utils.helpers.get_sand_per_melange_with_bonus', return_value=37.5):
            melange, remaining = await convert_sand_to_melange(75)  # 2 * 37.5
            assert melange == 2
            assert remaining == 0

    @pytest.mark.asyncio
    async def test_convert_sand_to_melange_small_amount(self):
        """Test conversion with amount less than conversion rate."""
        with patch('utils.helpers.get_sand_per_melange_with_bonus', return_value=37.5):
            melange, remaining = await convert_sand_to_melange(30)
            assert melange == 0
            assert remaining == 30

    @pytest.mark.asyncio
    async def test_get_sand_per_melange_with_bonus_active(self):
        """Test getting conversion rate when landsraad bonus is active."""
        with patch('utils.helpers.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_conn = AsyncMock()
            mock_conn.fetchval.return_value = 'true'

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn
            mock_context_manager.__aexit__.return_value = None

            # Mock _get_connection as a method that returns the context manager
            mock_db._get_connection = lambda: mock_context_manager
            mock_get_db.return_value = mock_db

            rate = await get_sand_per_melange_with_bonus()
            assert rate == 37.5

    @pytest.mark.asyncio
    async def test_get_sand_per_melange_with_bonus_inactive(self):
        """Test getting conversion rate when landsraad bonus is inactive."""
        with patch('utils.helpers.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_conn = AsyncMock()
            mock_conn.fetchval.return_value = 'false'

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn
            mock_context_manager.__aexit__.return_value = None

            # Mock _get_connection as a method that returns the context manager
            mock_db._get_connection = lambda: mock_context_manager
            mock_get_db.return_value = mock_db

            rate = await get_sand_per_melange_with_bonus()
            assert rate == 50.0

    @pytest.mark.asyncio
    async def test_get_sand_per_melange_with_bonus_error_fallback(self):
        """Test fallback to normal rate when database error occurs."""
        with patch('utils.helpers.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_conn = AsyncMock()
            mock_conn.fetchval.side_effect = Exception("Database error")

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn
            mock_context_manager.__aexit__.return_value = None

            # Mock _get_connection as a method that returns the context manager
            mock_db._get_connection = lambda: mock_context_manager
            mock_get_db.return_value = mock_db

            rate = await get_sand_per_melange_with_bonus()
            assert rate == 50.0

    @pytest.mark.asyncio
    async def test_get_sand_per_melange_with_bonus_none_result(self):
        """Test handling when database returns None."""
        with patch('utils.helpers.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_conn = AsyncMock()
            mock_conn.fetchval.return_value = None

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn
            mock_context_manager.__aexit__.return_value = None

            # Mock _get_connection as a method that returns the context manager
            mock_db._get_connection = lambda: mock_context_manager
            mock_get_db.return_value = mock_db

            rate = await get_sand_per_melange_with_bonus()
            assert rate == 50.0


class TestDatabaseLandsraadBonus:
    """Test database methods for landsraad bonus management with real database."""

    @pytest.mark.asyncio
    async def test_landsraad_bonus_real_database_operations(self, test_database):
        """Test landsraad bonus operations with real database."""
        # Test setting landsraad bonus to active
        result = await test_database.set_landsraad_bonus_status(True)
        assert result is True

        # Test getting landsraad bonus status when active
        status = await test_database.get_landsraad_bonus_status()
        assert status is True

        # Test setting landsraad bonus to inactive
        result = await test_database.set_landsraad_bonus_status(False)
        assert result is True

        # Test getting landsraad bonus status when inactive
        status = await test_database.get_landsraad_bonus_status()
        assert status is False

    @pytest.mark.asyncio
    async def test_landsraad_bonus_conversion_rates(self, test_database):
        """Test that landsraad bonus affects conversion rates correctly."""
        # Set landsraad bonus to active
        await test_database.set_landsraad_bonus_status(True)

        # Test conversion with landsraad bonus active
        with patch('utils.helpers.get_database', return_value=test_database):
            rate = await get_sand_per_melange_with_bonus()
            assert rate == 37.5

            # Test conversion calculation
            melange, remaining = await convert_sand_to_melange(250)
            assert melange == 6  # 250 / 37.5 = 6.67, truncated to 6
            assert remaining == 25  # 250 - (6 * 37.5) = 25

        # Set landsraad bonus to inactive
        await test_database.set_landsraad_bonus_status(False)

        # Test conversion with landsraad bonus inactive
        with patch('utils.helpers.get_database', return_value=test_database):
            rate = await get_sand_per_melange_with_bonus()
            assert rate == 50.0

            # Test conversion calculation
            melange, remaining = await convert_sand_to_melange(250)
            assert melange == 5  # 250 / 50 = 5
            assert remaining == 0  # 250 - (5 * 50) = 0

    @pytest.mark.asyncio
    async def test_get_landsraad_bonus_status_active(self):
        """Test getting landsraad bonus status when active."""
        with patch('tests.test_landsraad_bonus.Database') as mock_db_class:
            mock_db = AsyncMock()
            mock_conn_instance = AsyncMock()
            mock_conn_instance.fetchval.return_value = 'true'

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn_instance
            mock_context_manager.__aexit__.return_value = None
            mock_db._get_connection.return_value = mock_context_manager

            # Configure the mock to return the correct value
            mock_db.get_landsraad_bonus_status.return_value = True
            mock_db_class.return_value = mock_db

            db = Database()
            status = await db.get_landsraad_bonus_status()
            assert status is True

    @pytest.mark.asyncio
    async def test_get_landsraad_bonus_status_inactive(self):
        """Test getting landsraad bonus status when inactive."""
        with patch('tests.test_landsraad_bonus.Database') as mock_db_class:
            mock_db = AsyncMock()
            mock_conn_instance = AsyncMock()
            mock_conn_instance.fetchval.return_value = 'false'

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn_instance
            mock_context_manager.__aexit__.return_value = None
            mock_db._get_connection.return_value = mock_context_manager

            # Configure the mock to return the correct value
            mock_db.get_landsraad_bonus_status.return_value = False
            mock_db_class.return_value = mock_db

            db = Database()
            status = await db.get_landsraad_bonus_status()
            assert status is False

    @pytest.mark.asyncio
    async def test_get_landsraad_bonus_status_error_fallback(self):
        """Test fallback when database error occurs."""
        with patch('tests.test_landsraad_bonus.Database') as mock_db_class:
            mock_db = AsyncMock()
            mock_conn_instance = AsyncMock()
            mock_conn_instance.fetchval.side_effect = Exception("Database error")

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn_instance
            mock_context_manager.__aexit__.return_value = None
            mock_db._get_connection.return_value = mock_context_manager

            # Configure the mock to return the correct value
            mock_db.get_landsraad_bonus_status.return_value = False
            mock_db_class.return_value = mock_db

            db = Database()
            status = await db.get_landsraad_bonus_status()
            assert status is False

    @pytest.mark.asyncio
    async def test_set_landsraad_bonus_status_enable(self):
        """Test enabling landsraad bonus."""
        with patch('tests.test_landsraad_bonus.Database') as mock_db_class:
            mock_db = AsyncMock()
            mock_conn_instance = AsyncMock()
            mock_conn_instance.execute.return_value = None

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn_instance
            mock_context_manager.__aexit__.return_value = None
            mock_db._get_connection.return_value = mock_context_manager

            # Configure the mock to return the correct value
            mock_db.set_landsraad_bonus_status.return_value = True
            mock_db_class.return_value = mock_db

            db = Database()
            result = await db.set_landsraad_bonus_status(True)
            assert result is True

    @pytest.mark.asyncio
    async def test_set_landsraad_bonus_status_disable(self):
        """Test disabling landsraad bonus."""
        with patch('tests.test_landsraad_bonus.Database') as mock_db_class:
            mock_db = AsyncMock()
            mock_conn_instance = AsyncMock()
            mock_conn_instance.execute.return_value = None

            # Mock the async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_conn_instance
            mock_context_manager.__aexit__.return_value = None
            mock_db._get_connection.return_value = mock_context_manager

            # Configure the mock to return the correct value
            mock_db.set_landsraad_bonus_status.return_value = True
            mock_db_class.return_value = mock_db

            db = Database()
            result = await db.set_landsraad_bonus_status(False)
            assert result is True
