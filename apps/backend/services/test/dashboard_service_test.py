import pytest
from unittest.mock import patch, MagicMock
import services.dashboard_service as dashboard_service
from .conftest import SNAPSHOT, _iso


@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
@patch("services.dashboard_service._probe_ollama")
def test_get_services_status_running(mock_probe, mock_repo, mock_collector):
    mock_probe.return_value = {"reachable": False, "serverUrl": None, "serverIp": None, "isLan": False}
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
    mock_probe.return_value = {"reachable": True, "serverUrl": "http://192.168.1.45:11434", "serverIp": "192.168.1.45", "isLan": True}
    mock_repo.read_recent_errors.return_value = []
    mock_repo.read_last_activity.return_value = None
    mock_repo.check_ollama_errors.return_value = []
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = SNAPSHOT

    result = dashboard_service.get_services_status()

    assert result["ollama"]["reachable"] is True
    assert result["ollama"]["serverIp"] == "192.168.1.45"
    assert result["ollama"]["isLan"] is True


@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
@patch("services.dashboard_service._probe_ollama")
def test_get_services_status_ollama_unreachable(mock_probe, mock_repo, mock_collector):
    mock_probe.return_value = {"reachable": False, "serverUrl": "http://192.168.1.45:11434", "serverIp": "192.168.1.45", "isLan": True}
    mock_repo.read_recent_errors.return_value = []
    mock_repo.read_last_activity.return_value = None
    mock_repo.check_ollama_errors.return_value = [
        {"event": "ollama.ping_failed", "module": "aienrich", "message": "connection refused"}
    ]
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = SNAPSHOT

    result = dashboard_service.get_services_status()

    assert result["ollama"]["reachable"] is False
    assert result["ollama"]["serverIp"] == "192.168.1.45"
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
    from .conftest import _iso
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
