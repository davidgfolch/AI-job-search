import pytest
from unittest.mock import patch, MagicMock
from commonlib.terminalUtil import consoleTimer, Spinner, consoleTimerDocker


class TestSpinner:
    def test_init(self):
        spinner = Spinner()
        assert spinner.spinner in Spinner.SPINNERS

    def test_nextTick_wraps(self):
        spinner = Spinner()
        spinner.spinItem = len(spinner.spinner) - 1
        spinner.nextTick()
        assert spinner.spinItem == 0

    def test_generate(self):
        spinner = Spinner()
        result = spinner.generate()
        assert len(result) == 5


class TestTerminalFunctions:
    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer(self, mock_wakeable_timer):
        consoleTimer('Test message', '2s')
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

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer_docker(self, mock_wakeable_timer):
        with patch('commonlib.terminalUtil.isDocker', return_value=True):
            consoleTimer('Test message', '2s')
            assert mock_wakeable_timer.return_value.wait.called

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer_local(self, mock_wakeable_timer):
        with patch('commonlib.terminalUtil.isDocker', return_value=False):
            consoleTimer('Test message', '1s')
            assert mock_wakeable_timer.return_value.wait.called

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_consoleTimerDocker(self, mock_wakeable_timer):
        consoleTimerDocker('Test', '2s')
        assert mock_wakeable_timer.return_value.wait.called

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer_custom_end(self, mock_wakeable_timer):
        with patch('commonlib.terminalUtil.isDocker', return_value=False):
            consoleTimer('Test', '1s', end='\n')
            assert mock_wakeable_timer.return_value.wait.called
