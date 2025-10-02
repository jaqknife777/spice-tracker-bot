import pytest
import time
from unittest.mock import patch, AsyncMock
from commands.payroll import payroll

@pytest.fixture(autouse=True)
def mock_get_db(mocker, test_database):
    """Fixture to automatically mock get_database in the payroll command module."""
    mocker.patch('commands.payroll.get_database', return_value=test_database, create=True)

class TestPayrollCommand:
    @pytest.mark.asyncio
    async def test_payroll_confirm_false(self, mock_interaction, test_database):
        with patch('commands.payroll.send_response', new_callable=AsyncMock) as mock_send, \
             patch.object(test_database, 'pay_all_pending_melange', new_callable=AsyncMock) as mock_pay_all:
            await payroll.__wrapped__(mock_interaction, time.time(), confirm=False, use_followup=True)
            mock_pay_all.assert_not_called()
            mock_send.assert_called_once()
            kwargs = mock_send.call_args.kwargs
            assert "Payroll Cancelled" in kwargs['embed'].title
            assert kwargs['ephemeral'] is True

    @pytest.mark.asyncio
    async def test_payroll_confirm_true(self, mock_interaction, test_database):
        with patch('commands.payroll.send_response', new_callable=AsyncMock) as mock_send, \
             patch.object(test_database, 'pay_all_pending_melange', new_callable=AsyncMock) as mock_pay_all:
            mock_pay_all.return_value = {
                'users_paid': 2,
                'total_paid': 700,
                'paid_users': [
                    {'username': 'UserA', 'amount_paid': 500},
                    {'username': 'UserB', 'amount_paid': 200}
                ]
            }
            async def timed_op_side_effect(name, coro, *args, **kwargs):
                res = await coro(*args, **kwargs)
                return res, 0.1
            with patch('commands.payroll.timed_database_operation', side_effect=timed_op_side_effect):
                await payroll.__wrapped__(mock_interaction, time.time(), confirm=True, use_followup=True)
            mock_pay_all.assert_called_once()
            mock_send.assert_called_once()
            kwargs = mock_send.call_args.kwargs
            embed = kwargs['embed']
            assert "Guild Payroll Complete" in embed.title
            assert "700" in embed.fields[0].value
            assert "💸 Paid Users" in embed.fields[1].name
            assert "UserA**: 500" in embed.fields[1].value
            assert "UserB**: 200" in embed.fields[1].value

    @pytest.mark.asyncio
    async def test_payroll_confirm_true_no_one_to_pay(self, mock_interaction, test_database):
        with patch('commands.payroll.send_response', new_callable=AsyncMock) as mock_send, \
             patch.object(test_database, 'pay_all_pending_melange', new_callable=AsyncMock) as mock_pay_all:
            mock_pay_all.return_value = {'users_paid': 0, 'total_paid': 0, 'paid_users': []}
            async def timed_op_side_effect(name, coro, *args, **kwargs):
                res = await coro(*args, **kwargs)
                return res, 0.1
            with patch('commands.payroll.timed_database_operation', side_effect=timed_op_side_effect):
                await payroll.__wrapped__(mock_interaction, time.time(), confirm=True, use_followup=True)
            mock_pay_all.assert_called_once()
            mock_send.assert_called_once()
            kwargs = mock_send.call_args.kwargs
            assert "Payroll Status" in kwargs['embed'].title
            assert "There are no users with pending melange to pay" in kwargs['embed'].description