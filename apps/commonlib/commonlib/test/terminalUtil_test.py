import pytest
from unittest.mock import patch, MagicMock
from structlog.testing import capture_logs
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
    def test_console_timer_docker_emits_single_timer_record(self, mock_wakeable_timer):
        with capture_logs() as records:
            consoleTimerDocker('All jobs enriched. ', '1s')
        timer_records = [r for r in records if r['event'].startswith('timer.')]
        assert [r['event'] for r in timer_records] == ['timer.started']
        assert 'in_place' not in timer_records[0]
        assert timer_records[0]['message'] == 'All jobs enriched. '

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_console_timer_custom_end(self, mock_wakeable_timer):
        with patch('commonlib.terminalUtil.isDocker', return_value=False):
            consoleTimer('Test', '1s', end='\n')
            assert mock_wakeable_timer.return_value.wait.called

    @patch('commonlib.terminalUtil.WakeableTimer')
    def test_timer_events_strip_ansi(self, mock_wakeable_timer):
        with patch('commonlib.terminalUtil.isDocker', return_value=False), \
             capture_logs() as records:
            consoleTimer('\x1b[96mAll jobs enriched. \x1b[0m', '1s')
        timer_records = [r for r in records if r['event'].startswith('timer.')]
        assert timer_records
        for record in timer_records:
            assert '\x1b' not in record['message']
            assert record['message'] == 'All jobs enriched. '
