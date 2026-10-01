import pytest
from structlog.testing import capture_logs
from unittest.mock import patch, MagicMock
from .. import main


@pytest.fixture
def enabled():
    with patch("aiCvMatcher.main.getEnvBool", return_value=True), patch("aiCvMatcher.main.configure_logging") as configure:
        yield configure


def app_events(logs):
    return [entry for entry in logs if entry["event"].startswith("app.")]


def test_run_configures_logging_before_first_event(enabled):
    matcher = MagicMock()
    matcher.process_db_jobs.side_effect = SystemExit
    with patch("aiCvMatcher.main.FastCVMatcher") as factory, capture_logs() as logs:
        factory.instance.return_value = matcher
        with pytest.raises(SystemExit):
            main.run()
    enabled.assert_called_once_with("aiCvMatcher")
    started = app_events(logs)
    assert [entry["event"] for entry in started] == ["app.started"]
    assert started[0]["module"] == "aiCvMatcher.main"
    assert started[0]["log_level"] == "info"
    assert started[0]["version"]


def test_run_logs_disabled_and_exits():
    with patch("aiCvMatcher.main.getEnvBool", return_value=False), capture_logs() as logs:
        with pytest.raises(SystemExit):
            main.run()
    events = app_events(logs)
    assert [entry["event"] for entry in events] == ["app.started", "app.disabled"]
    assert events[1]["flag"] == "AI_CVMATCHER_ENABLED"
    assert events[1]["module"] == "aiCvMatcher.main"


def test_run_polls_and_renders_countdown(enabled):
    matcher = MagicMock()
    matcher.process_db_jobs.side_effect = [1, 0, SystemExit]
    with patch("aiCvMatcher.main.FastCVMatcher") as factory, patch("aiCvMatcher.main.consoleTimer") as timer, capture_logs() as logs:
        factory.instance.return_value = matcher
        with pytest.raises(SystemExit):
            main.run()
    factory.instance.assert_called_once_with()
    assert matcher.process_db_jobs.call_count == 3
    assert len(timer.call_args.args) == 2
    assert timer.call_args.kwargs == {"end": "\r"}
    assert set(app_events(logs)[0]) - {"event", "log_level", "module", "timestamp"} == {"version"}
