import pytest
from unittest.mock import patch
from commonlib.terminalUtil import consoleTimer

class TestTerminalFunctions:
    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer(self, mock_wakeable_timer):
        consoleTimer('Test message', '2s')
        # consoleTimer uses Spinner with tickXSec=6, so it calls wait multiple times
        assert mock_wakeable_timer.return_value.wait.called

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer_minutes(self, mock_wakeable_timer):
        consoleTimer('Test message', '1m')
        assert mock_wakeable_timer.return_value.wait.called

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer_hours(self, mock_wakeable_timer):
        consoleTimer('Test message', '1h')
        assert mock_wakeable_timer.return_value.wait.called

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer_invalid_format(self, mock_wakeable_timer):
        with pytest.raises((KeyError, ValueError)):
            consoleTimer('Test message', 'invalid')
