import pytest
from unittest.mock import patch
import services.dashboard_service as dashboard_service
from .conftest import SNAPSHOT, _iso, infrastructure


def _setup(mock_repo, mock_collector, mock_infra, infra=None, errors=None):
    mock_infra.return_value = infra or infrastructure()
    mock_repo.read_recent_errors.return_value = errors or []
    mock_repo.read_last_activity.return_value = None
    mock_repo.check_ollama_errors.return_value = []
    mock_collector.return_value.reload.return_value = None
    mock_collector.return_value.get_snapshot.return_value = SNAPSHOT


@patch("services.dashboard_service.get_infrastructure_status")
@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_running(mock_repo, mock_collector, mock_infra):
    _setup(mock_repo, mock_collector, mock_infra)

    result = dashboard_service.get_services_status()

    assert "services" in result
    assert "infrastructure" in result
    assert result["llmBackend"] == dashboard_service.LLM_BACKEND
    services = result["services"]
    assert len(services) == 3
    names = [s["name"] for s in services]
    assert names == ["aienrich", "aienrichskill", "aicvmatcher"]
    aienrich = services[0]
    assert aienrich["status"] == "running"
    assert aienrich["usesOllama"] is True
    assert aienrich["metrics"]["processed"] == 10
    assert aienrich["metrics"]["failed"] == 2


@patch("services.dashboard_service.get_infrastructure_status")
@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_exposes_all_infrastructure(mock_repo, mock_collector, mock_infra):
    _setup(mock_repo, mock_collector, mock_infra)

    result = dashboard_service.get_services_status()

    assert [e["name"] for e in result["infrastructure"]] == [
        "ollama", "backend", "web", "mysql", "mongo", "aiformfiller", "cron", "scrapper", "prometheus", "grafana"
    ]
    assert result["prometheus"] == {"reachable": True, "url": "http://localhost:9090"}
    assert result["grafana"] == {"reachable": True, "url": "http://localhost:3000"}


@patch("services.dashboard_service.get_infrastructure_status")
@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_ollama_reachable(mock_repo, mock_collector, mock_infra):
    _setup(mock_repo, mock_collector, mock_infra, infrastructure(
        reachable=True, serverUrl="http://192.168.1.45:11434", serverIp="192.168.1.45", isLan=True
    ))

    result = dashboard_service.get_services_status()

    assert result["ollama"]["reachable"] is True
    assert result["ollama"]["serverIp"] == "192.168.1.45"
    assert result["ollama"]["isLan"] is True


@patch("services.dashboard_service.get_infrastructure_status")
@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_ollama_unreachable(mock_repo, mock_collector, mock_infra):
    ollama_errors = [{"event": "ollama.ping_failed", "module": "aienrich", "message": "connection refused"}]
    _setup(mock_repo, mock_collector, mock_infra, infrastructure(
        reachable=False, serverUrl="http://192.168.1.45:11434", serverIp="192.168.1.45", isLan=True,
        recentErrors=ollama_errors
    ))

    result = dashboard_service.get_services_status()

    assert result["ollama"]["reachable"] is False
    assert result["ollama"]["serverIp"] == "192.168.1.45"
    assert len(result["ollama"]["recentErrors"]) == 1


@patch("services.dashboard_service.get_infrastructure_status")
@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_reads_errors(mock_repo, mock_collector, mock_infra):
    errors = [{"timestamp": "2026-09-03T10:00:00", "event": "job.failed", "level": "error", "message": "boom"}]
    _setup(mock_repo, mock_collector, mock_infra, errors=errors)

    result = dashboard_service.get_services_status()

    aienrich = result["services"][0]
    assert len(aienrich["recentErrors"]) == 1
    assert aienrich["recentErrors"][0]["event"] == "job.failed"


@patch("services.dashboard_service.get_infrastructure_status")
@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_log_fallback(mock_repo, mock_collector, mock_infra):
    activity = _iso()
    _setup(mock_repo, mock_collector, mock_infra)
    mock_repo.read_last_activity.return_value = activity

    result = dashboard_service.get_services_status()

    by_name = {s["name"]: s for s in result["services"]}
    assert by_name["aicvmatcher"]["status"] == "running"
    assert by_name["aicvmatcher"]["lastActivity"] == activity


@pytest.mark.parametrize("module,module_metrics,log,expected_name", [
    ("aiEnrich", {"last_processed_at": _iso(-40)}, _iso(), "aienrich"),
    ("aiEnrichSkill", {"last_processed_at": None, "last_heartbeat_at": _iso()}, None, "aienrichskill"),
])
@patch("services.dashboard_service.get_infrastructure_status")
@patch("services.dashboard_service.MetricsCollector")
@patch("services.dashboard_service._repo")
def test_get_services_status_recent_activity_running(mock_repo, mock_collector, mock_infra, module, module_metrics, log, expected_name):
    _setup(mock_repo, mock_collector, mock_infra)
    mock_repo.read_last_activity.return_value = log
    snapshot = dict(SNAPSHOT)
    snapshot["modules"] = dict(SNAPSHOT["modules"])
    snapshot["modules"][module] = module_metrics
    mock_collector.return_value.get_snapshot.return_value = snapshot

    result = dashboard_service.get_services_status()

    assert {s["name"]: s["status"] for s in result["services"]}[expected_name] == "running"


def test_module_metric_key_mapping():
    assert dashboard_service.MODULE_METRIC_KEYS == {
        "aienrich": "aiEnrich",
        "aienrichskill": "aiEnrichSkill",
        "aicvmatcher": "aiCvMatcher",
    }
