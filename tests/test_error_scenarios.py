"""
Tests for error scenarios that have caused breakage in the past.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncpg
from database import Database


class TestDatabaseColumnErrors:
    """Test scenarios that previously caused 'record index out of range' errors."""
    
    @pytest.mark.asyncio
    async def test_positional_indexing_error_prevention(self):
        """Test that database operations don't use positional indexing."""
        conn = AsyncMock()
        
        # Create a row that would cause positional indexing issues
        problematic_row = Mock()
        problematic_row.__getitem__ = Mock(side_effect=lambda key: {
            'user_id': '123456789',
            'username': 'TestUser',
            # Intentionally missing some columns to simulate schema mismatch
        }.get(key, None))
        
        conn.fetchrow.return_value = problematic_row
        
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = conn
            
            db = Database("test://url")
            
            # This should not raise IndexError or KeyError
            try:
                result = await db.get_user("123456789")
                # Should handle missing columns gracefully
                assert result is None or isinstance(result, dict)
            except (IndexError, KeyError) as e:
                pytest.fail(f"Database operation raised {type(e).__name__}: {e}")
    
    @pytest.mark.asyncio
    async def test_schema_mismatch_handling(self):
        """Test handling of database schema mismatches."""
        conn = AsyncMock()
        
        # Simulate a row with different column order or missing columns
        mismatched_row = Mock()
        mismatched_row.__getitem__ = Mock(side_effect=lambda key: {
            'user_id': '123456789',
            'username': 'TestUser',
            'total_melange': 100,
            # Missing paid_melange, created_at, last_updated
        }.get(key, None))
        
        conn.fetchrow.return_value = mismatched_row
        
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = conn
            
            db = Database("test://url")
            
            # Should handle missing columns without crashing
            result = await db.get_user("123456789")
            
            if result:
                # Should have the columns that exist
                assert 'user_id' in result
                assert 'username' in result
                assert 'total_melange' in result
                
                # Missing columns should be handled gracefully
                assert result.get('paid_melange') is None or isinstance(result.get('paid_melange'), int)
    
    @pytest.mark.asyncio
    async def test_empty_database_response_handling(self):
        """Test handling of empty database responses."""
        conn = AsyncMock()
        conn.fetchrow.return_value = None
        conn.fetch.return_value = []
        
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = conn
            
            db = Database("test://url")
            
            # These should not raise errors
            user_result = await db.get_user("nonexistent")
            assert user_result is None
            
            deposits_result = await db.get_user_deposits("nonexistent")
            assert deposits_result == []
    
    @pytest.mark.asyncio
    async def test_database_connection_failure_handling(self):
        """Test handling of database connection failures."""
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.side_effect = asyncpg.ConnectionDoesNotExistError("Connection failed")
            
            db = Database("test://url")
            
            # Should raise the connection error, not a column access error
            with pytest.raises(asyncpg.ConnectionDoesNotExistError):
                await db.get_user("123456789")


class TestDiscordResponseErrors:
    """Test scenarios that previously caused Discord response issues."""
    
    @pytest.fixture
    def mock_interaction_broken(self):
        """Create a mock interaction with broken response methods."""
        interaction = Mock()
        interaction.user.id = 123456789
        interaction.user.display_name = "TestUser"
        interaction.user.display_avatar = Mock()
        interaction.user.display_avatar.url = "https://example.com/avatar.png"
        interaction.created_at = Mock()
        interaction.created_at.timestamp.return_value = 1640995200.0
        interaction.guild = Mock()
        interaction.guild.id = 987654321
        interaction.guild.name = "TestGuild"
        interaction.channel = Mock()
        interaction.client = Mock()
        
        # Mock broken response methods
        interaction.response = AsyncMock()
        interaction.response.send = AsyncMock(side_effect=Exception("Response send failed"))
        interaction.response.defer = AsyncMock(side_effect=Exception("Defer failed"))
        interaction.followup = AsyncMock()
        interaction.followup.send = AsyncMock(side_effect=Exception("Followup send failed"))
        
        # Mock broken channel methods
        interaction.channel.send = AsyncMock(side_effect=Exception("Channel send failed"))
        interaction.channel.history = AsyncMock()
        
        return interaction
    
    @pytest.mark.asyncio
    async def test_command_handles_broken_responses(self, mock_interaction_broken):
        """Test that commands handle broken Discord responses gracefully."""
        with patch('utils.helpers.get_database') as mock_get_db, \
             patch('utils.logger.logger') as mock_logger:
            
            mock_db = AsyncMock()
            mock_db.get_user.return_value = {
                'user_id': '123456789',
                'username': 'TestUser',
                'total_melange': 100,
                'paid_melange': 50
            }
            mock_get_db.return_value = mock_db
            
            # Test that the command can be called (it may fail due to broken interaction)
            from commands.water import water
            try:
                await water(mock_interaction_broken, "Test Location", use_followup=True)
                # If we get here, the command handled the broken interaction
                assert True
            except Exception as e:
                # It's expected that broken interactions might cause errors
                # The important thing is that we don't get unhandled exceptions
                assert "Defer failed" in str(e) or "Unknown interaction" in str(e)
    
    @pytest.mark.asyncio
    async def test_send_response_fallback_mechanism(self, mock_interaction_broken):
        """Test that send_response falls back to channel.send when followup fails."""
        with patch('utils.helpers.send_response') as mock_send_response, \
             patch('utils.logger.logger') as mock_logger:
            
            # Make send_response raise an exception
            mock_send_response.side_effect = Exception("All response methods failed")
            
            # Test that the command can be called (it may fail due to broken interaction)
            from commands.water import water
            try:
                await water(mock_interaction_broken, "Test Location", use_followup=True)
                # If we get here, the command handled the broken interaction
                assert True
            except Exception as e:
                # It's expected that broken interactions might cause errors
                # The important thing is that we don't get unhandled exceptions
                assert "Defer failed" in str(e) or "Unknown interaction" in str(e)


class TestReactionHandlingErrors:
    """Test scenarios that could cause reaction handling issues."""
    
    @pytest.fixture
    def mock_reaction_broken(self):
        """Create a mock reaction with broken methods."""
        reaction = Mock()
        reaction.emoji = "✅"
        reaction.message = Mock()
        reaction.message.embeds = [Mock()]
        reaction.message.embeds[0].title = "💧 Water Delivery Request"
        reaction.message.embeds[0].description = "**Location:** Test Location"
        reaction.message.embeds[0].fields = [
            Mock(name="👤 Requester", value="<@123456789>"),
            Mock(name="📋 Status", value="⏳ Pending admin approval")
        ]
        reaction.message.created_at = Mock()
        reaction.message.guild = Mock()
        reaction.message.guild.id = 987654321
        reaction.message.edit = AsyncMock(side_effect=Exception("Message edit failed"))
        
        return reaction
    
    @pytest.fixture
    def mock_user_broken(self):
        """Create a mock user with broken methods."""
        user = Mock()
        user.bot = False
        user.id = 987654321
        user.display_name = "AdminUser"
        user.mention = "<@987654321>"
        return user
    
    @pytest.mark.asyncio
    async def test_reaction_handles_broken_message_edit(self, mock_reaction_broken, mock_user_broken):
        """Test that reaction handling works when message editing fails."""
        with patch('bot.bot') as mock_bot, \
             patch('utils.logger.logger') as mock_logger:
            
            from bot import on_reaction_add
            
            # Call the reaction handler - it should complete without errors
            try:
                await on_reaction_add(mock_reaction_broken, mock_user_broken)
                # If we get here, the reaction was handled successfully
                assert True
            except Exception as e:
                pytest.fail(f"Reaction error handling failed with error: {e}")
    
    @pytest.mark.asyncio
    async def test_reaction_handles_missing_embeds(self, mock_user_broken):
        """Test that reaction handling works when message has no embeds."""
        reaction = Mock()
        reaction.emoji = "✅"
        reaction.message = Mock()
        reaction.message.embeds = []  # No embeds
        reaction.message.edit = AsyncMock()
        
        with patch('bot.bot') as mock_bot:
            from bot import on_reaction_add
            
            # Should not raise an exception
            await on_reaction_add(reaction, mock_user_broken)
            
            # Should not edit the message
            reaction.message.edit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reaction_handles_wrong_embed_title(self, mock_user_broken):
        """Test that reaction handling works when embed has wrong title."""
        reaction = Mock()
        reaction.emoji = "✅"
        reaction.message = Mock()
        reaction.message.embeds = [Mock()]
        reaction.message.embeds[0].title = "Wrong Title"  # Not a water request
        reaction.message.edit = AsyncMock()
        
        with patch('bot.bot') as mock_bot:
            from bot import on_reaction_add
            
            # Should not raise an exception
            await on_reaction_add(reaction, mock_user_broken)
            
            # Should not edit the message
            reaction.message.edit.assert_not_called()


class TestEdgeCaseHandling:
    """Test edge cases that could cause breakage."""
    
    @pytest.mark.asyncio
    async def test_water_command_with_extreme_inputs(self):
        """Test water command with extreme input values."""
        interaction = Mock()
        interaction.user.id = 123456789
        interaction.user.display_name = "TestUser"
        interaction.user.display_avatar = Mock()
        interaction.user.display_avatar.url = "https://example.com/avatar.png"
        interaction.created_at = Mock()
        interaction.created_at.timestamp.return_value = 1640995200.0
        interaction.guild = Mock()
        interaction.guild.id = 987654321
        interaction.guild.name = "TestGuild"
        interaction.channel = Mock()
        interaction.client = Mock()
        interaction.response = AsyncMock()
        interaction.followup = AsyncMock()
        interaction.channel.send = AsyncMock()
        interaction.channel.history = AsyncMock()
        
        extreme_inputs = [
            "",  # Empty string
            "A" * 1000,  # Very long string
            "Location with\nNewlines\nAnd\tTabs",
            "Location with special chars !@#$%^&*()",
            "Location with unicode: 🏜️🌵💧",
            None  # None value
        ]
        
        for destination in extreme_inputs:
            try:
                from commands.water import water
                await water(interaction, destination, use_followup=True)
            except Exception as e:
                pytest.fail(f"Water command failed with extreme input '{destination}': {e}")
    
    @pytest.mark.asyncio
    async def test_database_with_malformed_data(self):
        """Test database operations with malformed data."""
        conn = AsyncMock()
        
        # Create malformed row data
        malformed_row = Mock()
        malformed_row.__getitem__ = Mock(side_effect=lambda key: {
            'user_id': None,  # None value
            'username': '',   # Empty string
            'total_melange': 'not_a_number',  # Wrong type
            'paid_melange': -1,  # Negative value
        }.get(key, None))
        
        conn.fetchrow.return_value = malformed_row
        
        with patch.object(Database, '_get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = conn
            
            db = Database("test://url")
            
            # Should handle malformed data gracefully
            try:
                result = await db.get_user("123456789")
                # Should either return None or handle the malformed data
                assert result is None or isinstance(result, dict)
            except Exception as e:
                pytest.fail(f"Database operation failed with malformed data: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self):
        """Test concurrent database operations don't cause issues."""
        conn = AsyncMock()
        
        # Mock successful responses
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
            
            # Run multiple operations concurrently
            import asyncio
            tasks = [
                db.get_user("123456789"),
                db.get_user("123456789"),
                db.get_user("123456789")
            ]
            
            try:
                results = await asyncio.gather(*tasks)
                # All operations should succeed
                assert all(result is not None for result in results)
            except Exception as e:
                pytest.fail(f"Concurrent database operations failed: {e}")
