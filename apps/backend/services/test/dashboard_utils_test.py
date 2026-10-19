from datetime import datetime, timezone
from unittest.mock import patch
import pytest
import services.dashboard_utils as dashboard_utils
from .conftest import _iso


@pytest.mark.parametrize("last_processed,last_error_at,expected", [
    (_iso(), None, "running"), (_iso(-10), None, "running"), (_iso(-30), None, "stopped"),
    (_iso(), _iso(), "error"), (None, None, "stopped"), ("2026-09-14T14:00:00Z", None, "stopped"),
])
def test_determine_status(last_processed, last_error_at, expected):
    now = datetime.now(timezone.utc)
    result = dashboard_utils._determine_status(now, last_processed, last_error_at)
    assert result == expected


@pytest.mark.parametrize("backend,label", [
    ("ollama", "Ollama"), ("ollama_cloud", "Ollama Cloud"), ("openai", "OpenAI"),
    ("openrouter", "OpenRouter"), ("OPENROUTER", "OpenRouter"), ("custom_backend", "Custom Backend"),
])
@patch("services.dashboard_utils.getEnv")
def test_display_name_aienrich_backend(mock_env, backend, label):
    mock_env.return_value = backend
    assert dashboard_utils._display_name("aienrich") == f"AI Enrich ({label})"


@pytest.mark.parametrize("module,expected", [
    ("aienrichnew", "AI Enrich New (HF)"), ("aienrichskill", "AI Enrich Skill"),
    ("aienrich3", "AI Enrich 3 (CPU)"), ("aicvmatcher", "CV Matcher"), ("unknown", "unknown"),
])
def test_display_name_mapping(module, expected):
    assert dashboard_utils._display_name(module) == expected


@pytest.mark.parametrize("metrics,log,expected", [
    (_iso(-30), _iso(), "log"), (_iso(), _iso(-30), "metrics"), (None, None, None),
    ("garbage", None, None), (None, "garbage", None), ("garbage", "garbage", None),
    ("garbage", _iso(), "log"), (_iso(), "garbage", "metrics"), (None, _iso(-10), "log"), (_iso(-10), None, "metrics"),
])
def test_pick_freshest(metrics, log, expected):
    result = dashboard_utils._pick_freshest(metrics, log)
    if expected is None:
        assert result is None
    else:
        assert result == (log if expected == "log" else metrics)
