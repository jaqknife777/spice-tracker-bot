"""
Comprehensive database robustness tests to prevent column access issues.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncpg
from database import Database


class TestDatabaseColumnAccess:
    """Test that database operations use column names instead of positional indexing."""
    
    @pytest.fixture
    def mock_connection(self):
        """Create a mock database connection with realistic row data."""
        conn = AsyncMock()
        
        # Mock user row with all expected columns
        user_row = Mock()
        user_row.__getitem__ = Mock(side_effect=lambda key: {
            'user_id': '123456789',
            'username': 'TestUser',
            'total_melange': 100,
            'paid_melange': 50,
            'created_at': '2024-01-01T00:00:00Z',
            'last_updated': '2024-01-01T00:00:00Z'
        }.get(key, None))
        
        # Mock deposit row
        deposit_row = Mock()
        deposit_row.__getitem__ = Mock(side_effect=lambda key: {
            'id': 1,
            'user_id': '123456789',
            'username': 'TestUser',
            'sand_amount': 1000,
            'type': 'solo',
            'expedition_id': None,
            'created_at': '2024-01-01T00:00:00Z'
        }.get(key, None))
        
        conn.fetchrow.return_value = user_row
        conn.fetch.return_value = [deposit_row]
        
        return conn
    
    @pytest.mark.asyncio
    async def test_get_user_uses_column_names(self, mock_connection):
        """Test that get_user method uses column names instead of positional indexing."""
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            
            db = Database("test://url")
            result = await db.get_user("123456789")
            
            # Verify the result structure matches expected column names
            assert result is not None
            assert 'user_id' in result
            assert 'username' in result
            assert 'total_melange' in result
            assert 'paid_melange' in result
            assert 'created_at' in result
            assert 'last_updated' in result
            
            # Verify column access was used (not positional)
            assert result['user_id'] == '123456789'
            assert result['username'] == 'TestUser'
    
    @pytest.mark.asyncio
    async def test_get_user_deposits_uses_column_names(self, mock_connection):
        """Test that get_user_deposits method uses column names."""
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            
            db = Database("test://url")
            result = await db.get_user_deposits("123456789")
            
            # Verify the result structure
            assert isinstance(result, list)
            if result:  # If deposits exist
                deposit = result[0]
                assert 'id' in deposit
                assert 'user_id' in deposit
                assert 'username' in deposit
                assert 'sand_amount' in deposit
                assert 'type' in deposit
                assert 'expedition_id' in deposit
                assert 'created_at' in deposit
    
    @pytest.mark.asyncio
    async def test_database_handles_missing_columns_gracefully(self):
        """Test that database operations handle missing columns gracefully."""
        conn = AsyncMock()
        
        # Mock row with missing columns (simulating schema mismatch)
        incomplete_row = Mock()
        incomplete_row.__getitem__ = Mock(side_effect=lambda key: {
            'user_id': '123456789',
            'username': 'TestUser',
            # Missing other columns
        }.get(key, None))
        
        conn.fetchrow.return_value = incomplete_row
        
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = conn
            
            db = Database("test://url")
            
            # This should not raise "record index out of range" error
            # Instead, it should handle missing columns gracefully
            try:
                result = await db.get_user("123456789")
                # Should either return None or handle missing data gracefully
                assert result is None or isinstance(result, dict)
            except (IndexError, KeyError) as e:
                pytest.fail(f"Database operation raised {type(e).__name__}: {e}")
    
    @pytest.mark.asyncio
    async def test_database_handles_empty_results(self):
        """Test that database operations handle empty results gracefully."""
        conn = AsyncMock()
        conn.fetchrow.return_value = None  # No user found
        conn.fetch.return_value = []  # No deposits found
        
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = conn
            
            db = Database("test://url")
            
            # Test get_user with no results
            result = await db.get_user("nonexistent")
            assert result is None
            
            # Test get_user_deposits with no results
            deposits = await db.get_user_deposits("nonexistent")
            assert deposits == []
    
    @pytest.mark.asyncio
    async def test_database_handles_connection_errors(self):
        """Test that database operations handle connection errors gracefully."""
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.side_effect = asyncpg.ConnectionDoesNotExistError("Connection failed")
            
            db = Database("test://url")
            
            # Should raise the connection error, not a column access error
            with pytest.raises(asyncpg.ConnectionDoesNotExistError):
                await db.get_user("123456789")


class TestDatabaseSchemaCompatibility:
    """Test database operations against different schema versions."""
    
    @pytest.mark.asyncio
    async def test_user_schema_compatibility(self):
        """Test that user operations work with expected schema."""
        conn = AsyncMock()
        
        # Mock the expected user table schema
        user_row = Mock()
        user_row.__getitem__ = Mock(side_effect=lambda key: {
            'user_id': '123456789',
            'username': 'TestUser',
            'total_melange': 100,
            'paid_melange': 50,
            'created_at': '2024-01-01T00:00:00Z',
            'last_updated': '2024-01-01T00:00:00Z'
        }.get(key, None))
        
        conn.fetchrow.return_value = user_row
        
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = conn
            
            db = Database("test://url")
            result = await db.get_user("123456789")
            
            # Verify all expected columns are present
            expected_columns = ['user_id', 'username', 'total_melange', 'paid_melange', 'created_at', 'last_updated']
            for column in expected_columns:
                assert column in result, f"Missing expected column: {column}"
    
    @pytest.mark.asyncio
    async def test_deposits_schema_compatibility(self):
        """Test that deposits operations work with expected schema."""
        conn = AsyncMock()
        
        # Mock the expected deposits table schema
        deposit_row = Mock()
        deposit_row.__getitem__ = Mock(side_effect=lambda key: {
            'id': 1,
            'user_id': '123456789',
            'username': 'TestUser',
            'sand_amount': 1000,
            'type': 'solo',
            'expedition_id': None,
            'paid': False,
            'created_at': '2024-01-01T00:00:00Z',
            'paid_at': None
        }.get(key, None))
        
        conn.fetch.return_value = [deposit_row]
        
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = conn
            
            db = Database("test://url")
            result = await db.get_user_deposits("123456789")
            
            # Verify all expected columns are present
            expected_columns = ['id', 'user_id', 'username', 'sand_amount', 'type', 'expedition_id', 'created_at']
            if result:
                for column in expected_columns:
                    assert column in result[0], f"Missing expected column: {column}"


class TestDatabaseErrorHandling:
    """Test database error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_database_retry_logic(self):
        """Test that database operations retry on connection failures."""
        with patch.object(Database, '_get_connection') as mock_get_conn:
            # First call fails, second succeeds
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = None
            
            mock_get_conn.side_effect = [
                asyncpg.ConnectionDoesNotExistError("Connection failed"),
                mock_conn
            ]
            
            db = Database("test://url")
            
            # Should retry and eventually succeed
            result = await db.get_user("123456789")
            assert result is None  # User not found, but no error raised
    
    @pytest.mark.asyncio
    async def test_database_logging_on_errors(self):
        """Test that database errors are properly logged."""
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.side_effect = Exception("Database error")
            
            with patch('utils.logger.logger.database_operation') as mock_logger:
                db = Database("test://url")
                
                with pytest.raises(Exception):
                    await db.get_user("123456789")
                
                # Verify error was logged
                mock_logger.assert_called()
                call_args = mock_logger.call_args
                assert call_args[1]['success'] is False
                assert 'error' in call_args[1]
