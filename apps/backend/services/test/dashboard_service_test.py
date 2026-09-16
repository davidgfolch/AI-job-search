import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import services.dashboard_service as dashboard_service


def _iso(offset_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)).isoformat()


SNAPSHOT = {
    "timestamp": "2026-09-03T10:00:00",
    "modules": {
        "aiEnrich": {
            "jobs_processed": 10,
            "jobs_succeeded": 8,
            "jobs_failed": 2,
            "pending_jobs": 3,
            "last_processed_at": _iso(),
            "last_error_at": None,
            "last_error": None,
        },
        "aiEnrichNew": {},
    },
    "global": {},
}


@pytest.mark.parametrize("last_processed,last_error_at,expected", [
    (_iso(), None, "running"), (_iso(-10), None, "running"), (_iso(-30), None, "stopped"),
    (_iso(), _iso(), "error"), (None, None, "stopped"), ("2026-09-14T14:00:00Z", None, "stopped"),
])
def test_determine_status(last_processed, last_error_at, expected):
    now = datetime.now(timezone.utc)
    result = dashboard_service._determine_status(now, last_processed, last_error_at)
    assert result == expected


@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_running(mock_repo, mock_collector):
    mock_repo.read_recent_errors.return_value = []
    mock_repo.read_last_activity.return_value = None
    mock_repo.check_ollama_errors.return_value = []
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = SNAPSHOT

    result = dashboard_service.get_services_status()

    assert "services" in result
    assert "ollama" in result
    services = result["services"]
    assert len(services) == 5
    names = [s["name"] for s in services]
    assert names == ["aienrich", "aienrichnew", "aienrichskill", "aienrich3", "aicvmatcher"]
    aienrich = services[0]
    assert aienrich["status"] == "running"
    assert aienrich["usesOllama"] is True
    assert aienrich["metrics"]["processed"] == 10
    assert aienrich["metrics"]["failed"] == 2


@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
@patch("services.dashboard_service._probe_ollama")
def test_get_services_status_ollama_reachable(mock_probe, mock_repo, mock_collector):
    mock_probe.return_value = True
    mock_repo.read_recent_errors.return_value = []
    mock_repo.read_last_activity.return_value = None
    mock_repo.check_ollama_errors.return_value = []
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = SNAPSHOT

    result = dashboard_service.get_services_status()

    assert result["ollama"]["reachable"] is True


@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
@patch("services.dashboard_service._probe_ollama")
def test_get_services_status_ollama_unreachable(mock_probe, mock_repo, mock_collector):
    mock_probe.return_value = False
    mock_repo.read_recent_errors.return_value = []
    mock_repo.read_last_activity.return_value = None
    mock_repo.check_ollama_errors.return_value = [
        {"event": "ollama.ping_failed", "module": "aienrich", "message": "connection refused"}
    ]
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = SNAPSHOT

    result = dashboard_service.get_services_status()

    assert result["ollama"]["reachable"] is False
    assert len(result["ollama"]["recentErrors"]) == 1


@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_reads_errors(mock_repo, mock_collector):
    mock_repo.read_recent_errors.return_value = [
        {"timestamp": "2026-09-03T10:00:00", "event": "job.failed", "level": "error", "message": "boom"}
    ]
    mock_repo.read_last_activity.return_value = None
    mock_repo.check_ollama_errors.return_value = []
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = SNAPSHOT

    result = dashboard_service.get_services_status()

    aienrich = result["services"][0]
    assert len(aienrich["recentErrors"]) == 1
    assert aienrich["recentErrors"][0]["event"] == "job.failed"


@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_log_fallback(mock_repo, mock_collector):
    activity = _iso()
    mock_repo.read_recent_errors.return_value = []
    mock_repo.read_last_activity.return_value = activity
    mock_repo.check_ollama_errors.return_value = []
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = SNAPSHOT

    result = dashboard_service.get_services_status()

    by_name = {s["name"]: s for s in result["services"]}
    assert by_name["aicvmatcher"]["status"] == "running"
    assert by_name["aicvmatcher"]["lastActivity"] == activity


@pytest.mark.parametrize("backend,label", [
    ("ollama", "Ollama"), ("ollama_cloud", "Ollama Cloud"), ("openai", "OpenAI"),
    ("openrouter", "OpenRouter"), ("OPENROUTER", "OpenRouter"), ("custom_backend", "Custom Backend"),
])
@patch("services.dashboard_service.getEnv")
def test_display_name_aienrich_backend(mock_env, backend, label):
    mock_env.return_value = backend
    assert dashboard_service._display_name("aienrich") == f"AI Enrich ({label})"


@pytest.mark.parametrize("module,expected", [
    ("aienrichnew", "AI Enrich New (HF)"), ("aienrichskill", "AI Enrich Skill"),
    ("aienrich3", "AI Enrich 3 (CPU)"), ("aicvmatcher", "CV Matcher"), ("unknown", "unknown"),
])
def test_display_name_mapping(module, expected):
    assert dashboard_service._display_name(module) == expected


@pytest.mark.parametrize("metrics,log,expected", [
    (_iso(-30), _iso(), "log"), (_iso(), _iso(-30), "metrics"), (None, None, None),
    ("garbage", None, None), (None, "garbage", None), ("garbage", "garbage", None),
    ("garbage", _iso(), "log"), (_iso(), "garbage", "metrics"), (None, _iso(-10), "log"), (_iso(-10), None, "metrics"),
])
def test_pick_freshest(metrics, log, expected):
    result = dashboard_service._pick_freshest(metrics, log)
    if expected is None:
        assert result is None
    else:
        assert result == (log if expected == "log" else metrics)


@pytest.mark.parametrize("module,module_metrics,log,expected_name", [
    ("aiEnrich", {"last_processed_at": _iso(-40)}, _iso(), "aienrich"),
    ("aiEnrichSkill", {"last_processed_at": None, "last_heartbeat_at": _iso()}, None, "aienrichskill"),
])
@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_recent_activity_running(mock_repo, mock_collector, module, module_metrics, log, expected_name):
    mock_repo.read_recent_errors.return_value = []
    mock_repo.read_last_activity.return_value = log
    mock_repo.check_ollama_errors.return_value = []
    snapshot = dict(SNAPSHOT)
    snapshot["modules"] = dict(SNAPSHOT["modules"])
    snapshot["modules"][module] = module_metrics
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = snapshot

    result = dashboard_service.get_services_status()

    assert {s["name"]: s["status"] for s in result["services"]}[expected_name] == "running"


def test_module_metric_key_mapping():
    assert dashboard_service.MODULE_METRIC_KEYS == {
        "aienrich": "aiEnrich",
        "aienrichnew": "aiEnrichNew",
        "aienrichskill": "aiEnrichSkill",
        "aienrich3": "aiEnrich3",
        "aicvmatcher": "aiCvMatcher",
    }