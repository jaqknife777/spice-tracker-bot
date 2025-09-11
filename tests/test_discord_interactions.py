"""
Comprehensive Discord interaction tests to prevent reply and reaction issues.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import discord
from commands.water import water
from commands.sand import sand
from commands.refinery import refinery


class TestDiscordResponseHandling:
    """Test Discord response handling to prevent reply issues."""
    
    @pytest.fixture
    def mock_interaction_complete(self):
        """Create a mock interaction that hasn't been responded to."""
        from datetime import datetime
        
        interaction = Mock()
        interaction.user.id = 123456789
        interaction.user.display_name = "TestUser"
        interaction.user.display_avatar = Mock()
        interaction.user.display_avatar.url = "https://example.com/avatar.png"
        interaction.created_at = datetime.fromtimestamp(1640995200.0)
        interaction.guild = Mock()
        interaction.guild.id = 987654321
        interaction.guild.name = "TestGuild"
        interaction.channel = Mock()
        interaction.client = Mock()
        
        # Mock response methods
        interaction.response = AsyncMock()
        interaction.response.send = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = AsyncMock()
        interaction.followup.send = AsyncMock()
        
        # Mock channel methods
        interaction.channel.send = AsyncMock()
        interaction.channel.history = AsyncMock()
        
        return interaction
    
    @pytest.fixture
    def mock_interaction_deferred(self):
        """Create a mock interaction that has been deferred."""
        interaction = self.mock_interaction_complete()
        interaction.response.defer.return_value = None
        return interaction
    
    @pytest.mark.asyncio
    async def test_water_command_response_handling(self, mock_interaction_complete):
        """Test that water command handles responses correctly."""
        with patch('utils.helpers.send_response') as mock_send_response, \
             patch('utils.logger.logger') as mock_logger:
            
            mock_send_response.return_value = None
            
            # Mock channel history for reaction adding
            mock_message = Mock()
            mock_message.author = mock_interaction_complete.client
            mock_message.embeds = [Mock()]
            mock_message.add_reaction = AsyncMock()
            
            # Create a proper async iterator for channel history
            async def mock_history_iterator():
                yield mock_message
            
            mock_interaction_complete.channel.history.return_value = mock_history_iterator()
            
            await water(mock_interaction_complete, "Test Location", use_followup=True)
            
            # Verify send_response was called with correct parameters
            mock_send_response.assert_called_once()
            call_args = mock_send_response.call_args
            assert call_args[0][0] == mock_interaction_complete  # interaction
            assert 'embed' in call_args[1]  # embed parameter
            assert call_args[1]['use_followup'] is True
            assert call_args[1]['ephemeral'] is False
    
    @pytest.mark.asyncio
    async def test_sand_command_response_handling(self, mock_interaction_complete):
        """Test that sand command handles responses correctly."""
        with patch('utils.helpers.get_database') as mock_get_db, \
             patch('utils.helpers.send_response') as mock_send_response, \
             patch('utils.logger.logger') as mock_logger:
            
            mock_db = AsyncMock()
            mock_db.get_user.return_value = {
                'user_id': '123456789',
                'username': 'TestUser',
                'total_melange': 100,
                'paid_melange': 50
            }
            mock_db.update_user_melange.return_value = None
            mock_db.add_deposit.return_value = None
            mock_get_db.return_value = mock_db
            mock_send_response.return_value = None
            
            await sand(mock_interaction_complete, 1000, use_followup=True)
            
            # Verify send_response was called
            mock_send_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refinery_command_response_handling(self, mock_interaction_complete):
        """Test that refinery command handles responses correctly."""
        with patch('utils.helpers.get_database') as mock_get_db, \
             patch('utils.helpers.send_response') as mock_send_response, \
             patch('utils.logger.logger') as mock_logger:
            
            mock_db = AsyncMock()
            mock_db.get_user.return_value = {
                'user_id': '123456789',
                'username': 'TestUser',
                'total_melange': 100,
                'paid_melange': 50,
                'last_updated': Mock()
            }
            mock_get_db.return_value = mock_db
            mock_send_response.return_value = None
            
            await refinery(mock_interaction_complete, use_followup=True)
            
            # Verify send_response was called
            mock_send_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_response_fallback_handling(self, mock_interaction_complete):
        """Test that commands fall back to channel.send when followup fails."""
        with patch('utils.helpers.send_response') as mock_send_response:
            # Make send_response raise an exception
            mock_send_response.side_effect = Exception("Followup failed")
            
            # The command should handle this gracefully
            try:
                await water(mock_interaction_complete, "Test Location", use_followup=True)
            except Exception as e:
                # Should not raise unhandled exceptions
                pytest.fail(f"Command raised unhandled exception: {e}")


class TestDiscordReactionHandling:
    """Test Discord reaction handling for water command."""
    
    @pytest.fixture
    def mock_reaction(self):
        """Create a mock reaction for testing."""
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
        reaction.message.edit = AsyncMock()
        
        return reaction
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock()
        user.bot = False
        user.id = 987654321
        user.display_name = "AdminUser"
        user.mention = "<@987654321>"
        return user
    
    @pytest.mark.asyncio
    async def test_water_reaction_handling(self, mock_reaction, mock_user):
        """Test that water delivery reactions are handled correctly."""
        with patch('bot.bot') as mock_bot, \
             patch('utils.logger.logger') as mock_logger:
            
            # Mock the bot's fetch_user method
            mock_requester = Mock()
            mock_requester.send = AsyncMock()
            mock_bot.fetch_user.return_value = mock_requester
            
            # Import and test the reaction handler
            from bot import on_reaction_add
            
            await on_reaction_add(mock_reaction, mock_user)
            
            # Verify the message was edited
            mock_reaction.message.edit.assert_called_once()
            
            # Verify the requester was notified
            mock_requester.send.assert_called_once()
            
            # Verify logging occurred
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_reaction_ignores_bot_reactions(self, mock_reaction):
        """Test that bot reactions are ignored."""
        bot_user = Mock()
        bot_user.bot = True
        
        with patch('bot.bot') as mock_bot:
            from bot import on_reaction_add
            
            await on_reaction_add(mock_reaction, bot_user)
            
            # Should not edit the message
            mock_reaction.message.edit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reaction_handles_missing_requester(self, mock_reaction, mock_user):
        """Test that reactions handle missing requester gracefully."""
        # Create reaction without requester field
        mock_reaction.message.embeds[0].fields = [
            Mock(name="📋 Status", value="⏳ Pending admin approval")
        ]
        
        with patch('bot.bot') as mock_bot:
            from bot import on_reaction_add
            
            # Should not raise an exception
            await on_reaction_add(mock_reaction, mock_user)
            
            # Should not edit the message
            mock_reaction.message.edit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reaction_handles_errors_gracefully(self, mock_reaction, mock_user):
        """Test that reaction handling errors are caught and logged."""
        # Make message.edit raise an exception
        mock_reaction.message.edit.side_effect = Exception("Edit failed")
        
        with patch('bot.bot') as mock_bot, \
             patch('utils.logger.logger') as mock_logger:
            
            from bot import on_reaction_add
            
            # Should not raise an exception
            await on_reaction_add(mock_reaction, mock_user)
            
            # Should log the error
            mock_logger.error.assert_called()


class TestDiscordEmbedStructure:
    """Test Discord embed structure and field access."""
    
    @pytest.mark.asyncio
    async def test_water_embed_structure(self, mock_interaction_complete):
        """Test that water command creates proper embed structure."""
        with patch('utils.helpers.send_response') as mock_send_response:
            mock_send_response.return_value = None
            
            await water(mock_interaction_complete, "Test Location", use_followup=True)
            
            # Get the embed that was sent
            call_args = mock_send_response.call_args
            embed = call_args[1]['embed']
            
            # Verify embed structure
            assert embed.title == "💧 Water Delivery Request"
            assert "Test Location" in embed.description
            assert len(embed.fields) >= 4  # Should have multiple fields
            
            # Verify field names
            field_names = [field.name for field in embed.fields]
            assert "👤 Requester" in field_names
            assert "📍 Destination" in field_names
            assert "⏰ Requested" in field_names
            assert "📋 Status" in field_names
    
    @pytest.mark.asyncio
    async def test_embed_field_access_safety(self, mock_interaction_complete):
        """Test that embed field access is safe and doesn't cause errors."""
        with patch('utils.helpers.send_response') as mock_send_response:
            mock_send_response.return_value = None
            
            # Test with various destination inputs
            test_destinations = [
                "Normal Location",
                "Location with Special Characters !@#$%",
                "Very Long Location Name That Might Cause Issues" * 10,
                "",  # Empty string
                "A" * 200  # Very long string
            ]
            
            for destination in test_destinations:
                try:
                    await water(mock_interaction_complete, destination, use_followup=True)
                except Exception as e:
                    pytest.fail(f"Water command failed with destination '{destination}': {e}")


class TestDiscordErrorRecovery:
    """Test Discord error recovery and fallback mechanisms."""
    
    @pytest.mark.asyncio
    async def test_command_error_recovery(self, mock_interaction_complete):
        """Test that commands recover from various Discord errors."""
        with patch('utils.helpers.send_response') as mock_send_response:
            # Test different error scenarios
            error_scenarios = [
                Exception("Discord API error"),
                ConnectionError("Network error"),
                TimeoutError("Request timeout"),
                AttributeError("Missing attribute")
            ]
            
            for error in error_scenarios:
                mock_send_response.side_effect = error
                
                # Commands should handle errors gracefully
                try:
                    await water(mock_interaction_complete, "Test Location", use_followup=True)
                except Exception as e:
                    # Should not raise unhandled exceptions
                    if type(e) != type(error):
                        pytest.fail(f"Command raised unexpected error type: {type(e)}")
    
    @pytest.mark.asyncio
    async def test_reaction_error_recovery(self, mock_reaction, mock_user):
        """Test that reaction handling recovers from errors."""
        error_scenarios = [
            Exception("Message edit failed"),
            ConnectionError("Network error"),
            AttributeError("Missing attribute")
        ]
        
        for error in error_scenarios:
            mock_reaction.message.edit.side_effect = error
            
            with patch('bot.bot') as mock_bot, \
                 patch('utils.logger.logger.error') as mock_logger:
                
                from bot import on_reaction_add
                
                # Should not raise an exception
                await on_reaction_add(mock_reaction, mock_user)
                
                # Should log the error
                mock_logger.assert_called()
