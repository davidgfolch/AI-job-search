import pytest
from unittest.mock import patch, MagicMock
from scrapper.core import utils
from scrapper.core.utils import debug, sleep, pageExists, abortExecution, runPreload
from scrapper.test.log_capture import captured_records, jsonl_records

class TestDebug:
    @pytest.mark.parametrize("debug_mode, exception, expected_events, expected_levels", [
        (False, False, ["debug.message"], ["error"]),
        (False, True, ["debug.interrupted"], ["error"]),
        (True, False, [], []),
        (True, True, ["debug.pause_requested"], ["warning"])
    ], ids=["message", "with_exception", "debug_pause", "debug_pause_exception"])
    def test_debug(self, debug_mode, exception, expected_events, expected_levels):
        with patch('builtins.input') as mock_input:
            with captured_records(utils, "scrapper.utils") as records:
                debug(debug_mode, 'Msg', exception=exception)
        assert [r["event"] for r in records] == expected_events
        assert [r["log_level"] for r in records] == expected_levels
        if expected_events:
            assert "Msg" in records[0]["message"]
        assert mock_input.called is debug_mode

    def test_debug_logs_traceback_from_caller_exception(self, tmp_path, monkeypatch):
        with jsonl_records(tmp_path, monkeypatch) as read:
            try:
                raise ValueError("boom")
            except ValueError:
                debug(False, 'Msg', exception=True)
        records = [r for r in read() if r["event"] == "debug.interrupted"]
        assert len(records) == 1
        assert records[0]["level"] == "error"
        assert "ValueError" in records[0]["exception"]
        assert records[0]["module"] == "scrapper.core.utils"


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
    @pytest.mark.parametrize("interrupted, expected_events, expected_values", [
        (True, ["scraper.interrupted", "scraper.stopping"], [True, True]),
        (False, ["scraper.interrupted"], [False]),
    ], ids=["keyboard_interrupt", "normal"])
    def test_abort_execution_events(self, interrupted, expected_events, expected_values):
        with patch('time.sleep', side_effect=KeyboardInterrupt if interrupted else None):
            with captured_records(utils, "scrapper.utils") as records:
                result = abortExecution()
        assert [r["event"] for r in records] == expected_events
        assert [r["log_level"] for r in records] == ["warning"] * len(expected_events)
        assert result is expected_values[-1]

    def test_abort_execution_wait_seconds_field(self):
        with patch('time.sleep'):
            with captured_records(utils, "scrapper.utils") as records:
                abortExecution()
        assert records[0]["wait_seconds"] == 3


class TestRunPreload:
    @pytest.mark.parametrize("props,expected", [
        ({}, True),
        ({'preloaded': True}, False),
    ])
    def test_run_preload(self, props, expected):
        assert runPreload(props) is expected
