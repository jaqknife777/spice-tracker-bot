"""
Integration tests for the bot system.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import discord
from discord.ext import commands

class TestBotIntegration:
    """Test bot integration and command registration."""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot instance."""
        bot = Mock(spec=commands.Bot)
        bot.tree = Mock()
        bot.tree.command = Mock()
        bot.tree.sync = AsyncMock()
        return bot
    
    def test_bot_import(self):
        """Test that the bot module can be imported."""
        import bot
        assert hasattr(bot, 'bot')
        assert hasattr(bot, 'register_commands')
    
    def test_command_registration_function_exists(self):
        """Test that the command registration function exists."""
        from bot import register_commands
        assert callable(register_commands)
    
    @patch('bot.bot')
    def test_command_registration_called(self, mock_bot, mock_bot_instance):
        """Test that command registration is called during bot startup."""
        # This would test the actual registration logic
        # For now, we just verify the function exists and is callable
        from bot import register_commands
        assert callable(register_commands)

class TestCommandPackageDiscovery:
    """Test the automatic command discovery system."""
    
    def test_commands_package_import(self):
        """Test that the commands package can be imported."""
        from commands import COMMAND_METADATA
        assert isinstance(COMMAND_METADATA, dict)
    
    def test_all_commands_have_metadata(self):
        """Test that all commands have proper metadata structure."""
        from commands import COMMAND_METADATA
        
        required_fields = ['aliases', 'description']
        
        for command_name, metadata in COMMAND_METADATA.items():
            for field in required_fields:
                assert field in metadata, f"Command {command_name} missing {field}"
                assert metadata[field] is not None, f"Command {command_name} has None {field}"
    
    def test_command_functions_are_callable(self):
        """Test that all command functions are callable."""
        from commands import COMMAND_METADATA
        
        for command_name in COMMAND_METADATA.keys():
            # Import the command function
            command_module = __import__(f'commands.{command_name}', fromlist=[command_name])
            command_func = getattr(command_module, command_name, None)
            
            assert command_func is not None, f"Command function {command_name} not found"
            assert callable(command_func), f"Command function {command_name} is not callable"

class TestUtilityIntegration:
    """Test utility module integration."""
    
    def test_utils_package_import(self):
        """Test that utility modules can be imported."""
        from utils import embed_builder, helpers, database_utils, decorators
        assert embed_builder is not None
        assert helpers is not None
        assert database_utils is not None
        assert decorators is not None
    
    def test_embed_builder_integration(self):
        """Test embed builder integration with Discord."""
        from utils.embed_builder import EmbedBuilder
        
        # Create a basic embed
        embed = EmbedBuilder("Test Title", "Test Description")
        embed.add_field("Test Field", "Test Value")
        
        # Build the embed (this should create a Discord Embed object)
        discord_embed = embed.build()
        
        # Verify it has the expected attributes
        assert hasattr(discord_embed, 'title')
        assert hasattr(discord_embed, 'description')
        assert hasattr(discord_embed, 'fields')
        assert discord_embed.title == "Test Title"
        assert discord_embed.description == "Test Description"
        assert len(discord_embed.fields) == 1

class TestDatabaseIntegration:
    """Test database integration."""
    
    @pytest.mark.asyncio
    async def test_database_module_import(self):
        """Test that the database module can be imported."""
        import database
        assert hasattr(database, 'Database')
    
    def test_database_class_structure(self):
        """Test that the Database class has required methods."""
        from database import Database
        
        # Check that required methods exist
        required_methods = [
            'initialize', 'upsert_user', 'add_deposit', 'get_user_stats',
            'update_user_melange', 'create_expedition'
        ]
        
        for method_name in required_methods:
            assert hasattr(Database, method_name), f"Database missing method: {method_name}"
            method = getattr(Database, method_name)
            assert callable(method), f"Database.{method_name} is not callable"

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_command_metadata_consistency(self):
        """Test that command metadata is consistent across all commands."""
        from commands import COMMAND_METADATA
        
        # Check for duplicate command names
        command_names = list(COMMAND_METADATA.keys())
        assert len(command_names) == len(set(command_names)), "Duplicate command names found"
        
        # Check for duplicate aliases across commands
        all_aliases = []
        for metadata in COMMAND_METADATA.values():
            all_aliases.extend(metadata['aliases'])
        
        # Filter out empty aliases
        non_empty_aliases = [alias for alias in all_aliases if alias]
        assert len(non_empty_aliases) == len(set(non_empty_aliases)), "Duplicate aliases found"
    
    def test_command_function_signatures(self):
        """Test that command functions have consistent signatures."""
        from commands import COMMAND_METADATA
        import inspect
        
        for command_name, metadata in COMMAND_METADATA.items():
            # Import the command function
            command_module = __import__(f'commands.{command_name}', fromlist=[command_name])
            command_func = getattr(command_module, command_name, None)
            
            if command_func:
                # Check that it's an async function
                assert inspect.iscoroutinefunction(command_func), f"Command {command_name} is not async"
                
                # Check that it takes at least interaction and use_followup parameters
                sig = inspect.signature(command_func)
                params = list(sig.parameters.keys())
                
                assert 'interaction' in params, f"Command {command_name} missing 'interaction' parameter"
                assert 'use_followup' in params, f"Command {command_name} missing 'use_followup' parameter"
