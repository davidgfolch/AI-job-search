import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.utils import debug, sleep, pageExists, abortExecution, runPreload

class TestDebug:
    @pytest.mark.parametrize("debug_mode, exception, input_se, print_count", [
        (False, False, None, 1),
        (False, True, None, 2),
        (True, False, [''], 0),
        (True, True, [''], 0)
    ])
    def test_debug(self, debug_mode, exception, input_se, print_count):
        with patch('builtins.print') as mp, patch('builtins.input', side_effect=input_se or []):
            debug(debug_mode, 'Msg', exception=exception)
            if not debug_mode: 
                assert mp.call_count >= print_count


class TestSleep:
    def test_sleep_normal(self):
        with patch('time.sleep') as mock_sleep, patch('random.uniform', return_value=0.5):
            sleep(0.1, 0.2)
            mock_sleep.assert_called_once_with(0.5)

    def test_sleep_disabled(self):
        with patch('time.sleep') as mock_sleep:
            result = sleep(0.1, 0.2, disable=True)
            mock_sleep.assert_not_called()
            assert result is None


class TestPageExists:
    @pytest.mark.parametrize("page, total, jobs_xpage, expected", [
        (1, 100, 10, False),
        (2, 100, 10, True),
        (11, 100, 10, False),
        (10, 100, 10, True),
    ])
    def test_page_exists(self, page, total, jobs_xpage, expected):
        assert pageExists(page, total, jobs_xpage) == expected


class TestAbortExecution:
    def test_abort_execution_keyboard_interrupt(self):
        with patch('time.sleep', side_effect=KeyboardInterrupt):
            result = abortExecution()
            assert result is True

    def test_abort_execution_normal(self):
        with patch('time.sleep'):
            result = abortExecution()
            assert result is False


class TestRunPreload:
    @pytest.mark.parametrize("props,expected", [
        ({}, True),
        ({'preloaded': True}, False),
        ({'preloaded': True, 'CLOSE_TAB': True}, True),
    ])
    def test_run_preload(self, props, expected):
        assert runPreload(props) is expected

    def test_run_preload_run_in_tabs_false(self):
        props = {'preloaded': True}
        assert runPreload(props, run_in_tabs=False) is True
