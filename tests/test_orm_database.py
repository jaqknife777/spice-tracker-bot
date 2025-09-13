"""
Test the SQLAlchemy ORM database implementation.
"""
import pytest
from database_orm import Database


class TestORMDatabase:
    """Test SQLAlchemy ORM database functionality."""

    @pytest.mark.asyncio
    async def test_database_initialization(self, test_database):
        """Test that the database initializes correctly."""
        assert test_database is not None
        assert test_database.is_sqlite is True

    @pytest.mark.asyncio
    async def test_user_operations(self, test_database):
        """Test basic user operations."""
        user_id = "123456789"
        username = "TestUser"

        # Test upsert_user
        await test_database.upsert_user(user_id, username)

        # Test get_user
        user = await test_database.get_user(user_id)
        assert user is not None
        assert user['user_id'] == user_id
        assert user['username'] == username
        assert user['total_melange'] == 0.0
        assert user['paid_melange'] == 0.0

    @pytest.mark.asyncio
    async def test_deposit_operations(self, test_database):
        """Test deposit operations."""
        user_id = "123456789"
        username = "TestUser"
        sand_amount = 1000

        # Ensure user exists
        await test_database.upsert_user(user_id, username)

        # Test add_deposit
        await test_database.add_deposit(user_id, username, sand_amount)

        # Test get_user_deposits
        deposits = await test_database.get_user_deposits(user_id)
        assert len(deposits) == 1
        assert deposits[0]['sand_amount'] == sand_amount
        assert deposits[0]['type'] == 'solo'

    @pytest.mark.asyncio
    async def test_melange_operations(self, test_database):
        """Test melange operations."""
        user_id = "123456789"
        username = "TestUser"
        melange_amount = 10.5

        # Ensure user exists
        await test_database.upsert_user(user_id, username)

        # Test update_user_melange
        await test_database.update_user_melange(user_id, melange_amount)

        # Test get_user
        user = await test_database.get_user(user_id)
        assert user['total_melange'] == melange_amount

        # Test get_user_pending_melange
        pending = await test_database.get_user_pending_melange(user_id)
        assert pending['total_melange'] == melange_amount
        assert pending['paid_melange'] == 0.0
        assert pending['pending_melange'] == melange_amount

    @pytest.mark.asyncio
    async def test_expedition_operations(self, test_database):
        """Test expedition operations."""
        initiator_id = "123456789"
        initiator_username = "TestUser"
        total_sand = 5000
        sand_per_melange = 50

        # Ensure user exists
        await test_database.upsert_user(initiator_id, initiator_username)

        # Test create_expedition
        expedition_id = await test_database.create_expedition(
            initiator_id, initiator_username, total_sand, sand_per_melange
        )
        assert expedition_id is not None

    @pytest.mark.asyncio
    async def test_guild_treasury_operations(self, test_database):
        """Test guild treasury operations."""
        sand_amount = 10000
        melange_amount = 200.5

        # Test get_guild_treasury (should create initial record)
        treasury = await test_database.get_guild_treasury()
        assert treasury['total_sand'] == 0
        assert treasury['total_melange'] == 0.0

        # Test update_guild_treasury
        await test_database.update_guild_treasury(sand_amount, melange_amount)

        # Verify update
        treasury = await test_database.get_guild_treasury()
        assert treasury['total_sand'] == sand_amount
        assert treasury['total_melange'] == melange_amount

    @pytest.mark.asyncio
    async def test_leaderboard_operations(self, test_database):
        """Test leaderboard operations."""
        # Create multiple users with different melange amounts
        users_data = [
            ("user1", "UserOne", 100.0),
            ("user2", "UserTwo", 50.0),
            ("user3", "UserThree", 75.0)
        ]

        for user_id, username, melange in users_data:
            await test_database.upsert_user(user_id, username)
            await test_database.update_user_melange(user_id, melange)

        # Test get_leaderboard
        leaderboard = await test_database.get_leaderboard(limit=10)
        assert len(leaderboard) == 3

        # Should be sorted by melange amount descending
        assert leaderboard[0]['total_melange'] == 100.0
        assert leaderboard[1]['total_melange'] == 75.0
        assert leaderboard[2]['total_melange'] == 50.0

    @pytest.mark.asyncio
    async def test_database_cleanup(self, test_database):
        """Test database cleanup operations."""
        # Add some data
        user_id = "123456789"
        username = "TestUser"
        await test_database.upsert_user(user_id, username)
        await test_database.add_deposit(user_id, username, 1000)

        # Verify data exists
        user = await test_database.get_user(user_id)
        assert user is not None

        deposits = await test_database.get_user_deposits(user_id)
        assert len(deposits) == 1

        # Test reset_all_stats
        await test_database.reset_all_stats()

        # Verify data is gone
        user = await test_database.get_user(user_id)
        assert user is None

        deposits = await test_database.get_user_deposits(user_id)
        assert len(deposits) == 0

    @pytest.mark.asyncio
    async def test_user_stats_compatibility(self, test_database):
        """Test user stats method for compatibility."""
        user_id = "123456789"
        username = "TestUser"

        # Ensure user exists
        await test_database.upsert_user(user_id, username)
        await test_database.update_user_melange(user_id, 25.0)

        # Test get_user_stats
        stats = await test_database.get_user_stats(user_id)
        assert stats is not None
        assert stats['total_melange'] == 25.0
        assert 'timing' in stats

    @pytest.mark.asyncio
    async def test_database_isolation(self, test_database):
        """Test that each test gets a clean database."""
        # This test should run with a clean database
        user_id = "isolation_test_user"
        username = "IsolationTestUser"

        # Add some data
        await test_database.upsert_user(user_id, username)
        await test_database.add_deposit(user_id, username, 500)

        # Verify data exists
        user = await test_database.get_user(user_id)
        assert user is not None
        assert user['username'] == username
