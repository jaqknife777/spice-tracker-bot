"""
Tests for bot commands.
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from commands import harvest, refinery, leaderboard, conversion, split, help, reset, ledger, expedition, payment, payroll

class TestHarvestCommand:
    """Test the harvest command."""
    
    @pytest.mark.asyncio
    async def test_harvest_valid_amount(self, mock_interaction, mock_database):
        """Test harvest command with valid amount."""
        with patch('commands.harvest.get_database', return_value=mock_database):
            with patch('commands.harvest.get_sand_per_melange', return_value=50):
                await harvest(mock_interaction, 1000, False)
                
                # Verify database calls
                mock_database.add_deposit.assert_called_once()
                mock_database.get_user_stats.assert_called_once()
                
                # Verify response was sent
                mock_interaction.response.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_harvest_invalid_amount_low(self, mock_interaction, mock_database):
        """Test harvest command with amount too low."""
        with patch('commands.harvest.get_database', return_value=mock_database):
            await harvest(mock_interaction, 0, False)
            
            # Verify error response
            mock_interaction.response.send.assert_called_once()
            call_args = mock_interaction.response.send.call_args[0][0]
            assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_harvest_invalid_amount_high(self, mock_interaction, mock_database):
        """Test harvest command with amount too high."""
        with patch('commands.harvest.get_database', return_value=mock_database):
            await harvest(mock_interaction, 15000, False)
            
            # Verify error response
            mock_interaction.response.send.assert_called_once()
            call_args = mock_interaction.response.send.call_args[0][0]
            assert "❌" in call_args

class TestRefineryCommand:
    """Test the refinery command."""
    
    @pytest.mark.asyncio
    async def test_refinery_command(self, mock_interaction, mock_database):
        """Test refinery command execution."""
        with patch('commands.refinery.get_database', return_value=mock_database):
            await refinery(mock_interaction, False)
            
            # Verify database calls
            mock_database.get_user_stats.assert_called_once()
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()

class TestLeaderboardCommand:
    """Test the leaderboard command."""
    
    @pytest.mark.asyncio
    async def test_leaderboard_default_limit(self, mock_interaction, mock_database):
        """Test leaderboard command with default limit."""
        with patch('commands.leaderboard.get_database', return_value=mock_database):
            mock_database.get_top_refiners.return_value = [
                {'username': 'User1', 'total_melange': 100},
                {'username': 'User2', 'total_melange': 50}
            ]
            
            await leaderboard(mock_interaction, 10, False)
            
            # Verify database calls
            mock_database.get_top_refiners.assert_called_once_with(10)
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()

class TestConversionCommand:
    """Test the conversion command."""
    
    @pytest.mark.asyncio
    async def test_conversion_command(self, mock_interaction):
        """Test conversion command execution."""
        with patch('commands.conversion.get_sand_per_melange', return_value=50):
            await conversion(mock_interaction, False)
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()

class TestSplitCommand:
    """Test the split command."""
    
    @pytest.mark.asyncio
    async def test_split_command(self, mock_interaction, mock_database):
        """Test split command execution."""
        with patch('commands.split.get_database', return_value=mock_database):
            await split(mock_interaction, 1000, 10.0, False)
            
            # Verify database calls
            mock_database.create_expedition.assert_called_once()
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()

class TestHelpCommand:
    """Test the help command."""
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_interaction):
        """Test help command execution."""
        await help(mock_interaction, False)
        
        # Verify response was sent
        mock_interaction.response.send.assert_called_once()

class TestResetCommand:
    """Test the reset command."""
    
    @pytest.mark.asyncio
    async def test_reset_command_confirmed(self, mock_interaction, mock_database):
        """Test reset command with confirmation."""
        with patch('commands.reset.get_database', return_value=mock_database):
            await reset(mock_interaction, True, False)
            
            # Verify database calls
            mock_database.reset_all_statistics.assert_called_once()
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_command_not_confirmed(self, mock_interaction, mock_database):
        """Test reset command without confirmation."""
        with patch('commands.reset.get_database', return_value=mock_database):
            await reset(mock_interaction, False, False)
            
            # Verify no database calls
            mock_database.reset_all_statistics.assert_not_called()
            
            # Verify warning response
            mock_interaction.response.send.assert_called_once()

class TestLedgerCommand:
    """Test the ledger command."""
    
    @pytest.mark.asyncio
    async def test_ledger_command(self, mock_interaction, mock_database):
        """Test ledger command execution."""
        with patch('commands.ledger.get_database', return_value=mock_database):
            await ledger(mock_interaction, False)
            
            # Verify database calls
            mock_database.get_user_deposits.assert_called_once()
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()

class TestExpeditionCommand:
    """Test the expedition command."""
    
    @pytest.mark.asyncio
    async def test_expedition_command(self, mock_interaction, mock_database):
        """Test expedition command execution."""
        with patch('commands.expedition.get_database', return_value=mock_database):
            await expedition(mock_interaction, 1, False)
            
            # Verify database calls
            mock_database.get_expedition_participants.assert_called_once()
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()

class TestPaymentCommand:
    """Test the payment command."""
    
    @pytest.mark.asyncio
    async def test_payment_command(self, mock_interaction, mock_database):
        """Test payment command execution."""
        mock_user = Mock()
        mock_user.id = 987654321
        mock_user.display_name = "TargetUser"
        
        with patch('commands.payment.get_database', return_value=mock_database):
            await payment(mock_interaction, mock_user, False)
            
            # Verify database calls
            mock_database.get_user_deposits.assert_called_once()
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()

class TestPayrollCommand:
    """Test the payroll command."""
    
    @pytest.mark.asyncio
    async def test_payroll_command(self, mock_interaction, mock_database):
        """Test payroll command execution."""
        with patch('commands.payroll.get_database', return_value=mock_database):
            await payroll(mock_interaction, False)
            
            # Verify database calls
            mock_database.get_all_unpaid_users.assert_called_once()
            
            # Verify response was sent
            mock_interaction.response.send.assert_called_once()
