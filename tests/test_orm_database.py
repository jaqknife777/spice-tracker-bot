"""
Test the SQLAlchemy ORM database implementation.
"""
import pytest
import pytest_asyncio
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
        assert user['total_melange'] == 0
        assert user['paid_melange'] == 0

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
        melange_amount = 10

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
        assert pending['paid_melange'] == 0
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

        # Test add_expedition_participant
        participant_id = "987654321"
        participant_username = "ParticipantUser"
        await test_database.upsert_user(participant_id, participant_username)
        await test_database.add_expedition_participant(
            expedition_id, participant_id, participant_username, 100, 2
        )

        # Test get_expedition_participants
        expedition_data = await test_database.get_expedition_participants(expedition_id)
        assert expedition_data is not None
        assert len(expedition_data['participants']) == 1
        assert expedition_data['participants'][0]['user_id'] == participant_id

    @pytest.mark.asyncio
    async def test_guild_treasury_operations(self, test_database):
        """Test guild treasury operations."""
        sand_amount = 10000
        melange_amount = 200

        # Test get_guild_treasury (should create initial record)
        treasury = await test_database.get_guild_treasury()
        assert treasury['total_sand'] == 0
        assert treasury['total_melange'] == 0

        # Test update_guild_treasry
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
            ("user1", "UserOne", 100),
            ("user2", "UserTwo", 50),
            ("user3", "UserThree", 75)
        ]

        for user_id, username, melange in users_data:
            await test_database.upsert_user(user_id, username)
            await test_database.update_user_melange(user_id, melange)

        # Test get_leaderboard
        leaderboard = await test_database.get_leaderboard(limit=10)
        assert len(leaderboard) == 3

        # Should be sorted by melange amount descending
        assert leaderboard[0]['total_melange'] == 100
        assert leaderboard[1]['total_melange'] == 75
        assert leaderboard[2]['total_melange'] == 50

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
        await test_database.update_user_melange(user_id, 25)

        # Test get_user_stats
        stats = await test_database.get_user_stats(user_id)
        assert stats is not None
        assert stats['total_melange'] == 25
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


class TestPaginatedDepositOperations:
    """Test paginated deposit operations."""

    @pytest_asyncio.fixture(scope="function")
    async def setup_deposits(self, test_database):
        """Setup a user with many deposits for pagination tests."""
        user_id = "pagination_user"
        username = "PaginationUser"
        await test_database.upsert_user(user_id, username)
        for i in range(25):
            await test_database.add_deposit(user_id, username, 100 + i, melange_amount=2, conversion_rate=50.0)
        return user_id

    @pytest.mark.asyncio
    async def test_get_user_deposits_count(self, test_database, setup_deposits):
        """Test counting user deposits."""
        user_id = setup_deposits
        count = await test_database.get_user_deposits_count(user_id)
        assert count == 25

    @pytest.mark.asyncio
    async def test_get_user_deposits_pagination(self, test_database, setup_deposits):
        """Test paginated fetching of user deposits."""
        user_id = setup_deposits

        # Test first page
        page1 = await test_database.get_user_deposits(user_id, page=1, per_page=10)
        assert len(page1) == 10
        assert page1[0]['sand_amount'] == 124 # Most recent deposit

        # Test second page
        page2 = await test_database.get_user_deposits(user_id, page=2, per_page=10)
        assert len(page2) == 10
        assert page2[0]['sand_amount'] == 114

        # Test last page
        page3 = await test_database.get_user_deposits(user_id, page=3, per_page=10)
        assert len(page3) == 5
        assert page3[0]['sand_amount'] == 104

        # Test out of bounds page
        page4 = await test_database.get_user_deposits(user_id, page=4, per_page=10)
        assert len(page4) == 0
