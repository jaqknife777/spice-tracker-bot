"""
Tests for utility modules and functions.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from utils.embed_builder import EmbedBuilder
from utils.helpers import get_database, get_sand_per_melange, send_response
from utils.database_utils import timed_database_operation, validate_user_exists
from utils.decorators import handle_interaction_expiration, monitor_performance

class TestEmbedBuilder:
    """Test the EmbedBuilder utility."""
    
    def test_embed_builder_creation(self):
        """Test creating a basic embed."""
        embed = EmbedBuilder("Test Title", description="Test Description")
        assert embed.embed.title == "Test Title"
        assert embed.embed.description == "Test Description"
    
    def test_embed_builder_with_fields(self):
        """Test adding fields to embed."""
        embed = EmbedBuilder("Test Title")
        embed.add_field("Field1", "Value1", inline=True)
        embed.add_field("Field2", "Value2", inline=False)
        
        built_embed = embed.build()
        assert len(built_embed.fields) == 2
        assert built_embed.fields[0].name == "Field1"
        assert built_embed.fields[0].value == "Value1"
        assert built_embed.fields[0].inline is True
    
    def test_embed_builder_with_footer(self):
        """Test adding footer to embed."""
        embed = EmbedBuilder("Test Title")
        embed.set_footer("Test Footer")
        
        built_embed = embed.build()
        assert built_embed.footer.text == "Test Footer"

class TestHelpers:
    """Test helper functions."""
    
    def test_get_sand_per_melange(self):
        """Test getting sand per melange conversion rate."""
        rate = get_sand_per_melange()
        assert isinstance(rate, int)
        assert rate > 0
    
    @pytest.mark.asyncio
    async def test_send_response_interaction(self, mock_interaction):
        """Test send_response with interaction."""
        await send_response(mock_interaction, "Test message", use_followup=False)
        
        # When use_followup=False, it calls channel.send, not response.send
        mock_interaction.channel.send.assert_called_once_with("Test message")
    
    @pytest.mark.asyncio
    async def test_send_response_followup(self, mock_interaction):
        """Test send_response with followup."""
        await send_response(mock_interaction, "Test message", use_followup=True)
        
        mock_interaction.followup.send.assert_called_once_with("Test message", ephemeral=False)
    
    @pytest.mark.asyncio
    async def test_send_response_with_embed(self, mock_interaction):
        """Test send_response with embed."""
        embed = EmbedBuilder("Test Title").build()
        await send_response(mock_interaction, embed=embed, use_followup=False)
        
        # When use_followup=False, it calls channel.send, not response.send
        mock_interaction.channel.send.assert_called_once_with(embed=embed)

class TestDatabaseUtils:
    """Test database utility functions."""
    
    @pytest.mark.asyncio
    async def test_timed_database_operation(self, mock_database):
        """Test timed database operation wrapper."""
        async def test_operation():
            return "success"
        
        result = await timed_database_operation("test_op", test_operation)
        
        # The function returns a tuple (result, execution_time)
        assert isinstance(result, tuple)
        assert result[0] == "success"
        assert isinstance(result[1], (int, float))
    
    @pytest.mark.asyncio
    async def test_validate_user_exists(self, mock_database):
        """Test user validation."""
        # First call returns None (user doesn't exist), second call returns the user
        mock_database.get_user.side_effect = [None, {"user_id": "123", "username": "TestUser"}]
        mock_database.upsert_user.return_value = {"user_id": "123", "username": "TestUser"}
        
        result = await validate_user_exists(mock_database, "123", "TestUser")
        
        assert result["user_id"] == "123"
        mock_database.upsert_user.assert_called_once_with("123", "TestUser")
        assert mock_database.get_user.call_count == 2  # Called twice: once to check, once after creation
    


class TestDecorators:
    """Test decorator functions."""
    
    @pytest.mark.asyncio
    async def test_handle_interaction_expiration(self, mock_interaction):
        """Test interaction expiration decorator."""
        @handle_interaction_expiration
        async def test_command(interaction, use_followup=False):
            return "success"
        
        result = await test_command(mock_interaction, False)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_monitor_performance(self):
        """Test performance monitoring decorator."""
        @monitor_performance("test_operation")
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"

class TestCommandMetadata:
    """Test command metadata structure."""
    
    def test_command_metadata_import(self):
        """Test that command metadata can be imported."""
        from commands import COMMAND_METADATA
        
        assert isinstance(COMMAND_METADATA, dict)
        assert len(COMMAND_METADATA) > 0
        
        # Check that all commands have required metadata fields
        for command_name, metadata in COMMAND_METADATA.items():
            assert 'aliases' in metadata
            assert 'description' in metadata
            assert isinstance(metadata['aliases'], list)
            assert isinstance(metadata['description'], str)
    
    def test_command_functions_import(self):
        """Test that command functions can be imported."""
        from commands import sand, refinery, leaderboard
        
        assert callable(sand)
        assert callable(refinery)
        assert callable(leaderboard)
