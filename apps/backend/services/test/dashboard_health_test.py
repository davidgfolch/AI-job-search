from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

import services.dashboard_health as health

HEALTH = "services.dashboard_health"


def _repo():
    repo = MagicMock()
    repo.read_last_activity.return_value = None
    repo.check_ollama_errors.return_value = []
    return repo


@contextmanager
def _probes(repo, *, http_result=None, mysql=(True, "SELECT 1 ok"), mongo=(True, "ping ok"), ollama=None):
    db_repo = MagicMock()
    db_repo.probe_mysql.return_value = mysql
    db_repo.probe_mongo.return_value = mongo
    db_repo.display_url.side_effect = lambda name, _uri: f"{name}://host"
    ollama = ollama or {"reachable": False, "serverUrl": None, "serverIp": None, "isLan": False}
    with patch(f"{HEALTH}.DashboardProbeRepository", return_value=db_repo), \
            patch(f"{HEALTH}.resolve_mongo_uri", return_value="mongodb://mongo_db:27017/"), \
            patch(f"{HEALTH}._probe_ollama", return_value=ollama), \
            patch(f"{HEALTH}._probe_service", return_value=http_result or {"reachable": True, "url": "http://service"}) as http_probe:
        yield http_probe


def test_infrastructure_covers_every_service():
    repo = _repo()
    with _probes(repo):
        entries = health.get_infrastructure_status(repo)
    assert [e["name"] for e in entries] == [
        "ollama", "backend", "web", "mysql", "mongo", "aiformfiller", "cron", "scrapper", "prometheus", "grafana"
    ]
    assert {e["kind"] for e in entries} == {"ollama", "http", "database", "activity"}
    repo.check_ollama_errors.assert_called_once()


def test_http_entries_probe_their_health_paths():
    repo = _repo()
    with _probes(repo) as http_probe:
        entries = health.get_infrastructure_status(repo)
    by_name = {e["name"]: e for e in entries}
    paths = [call.args[1] for call in http_probe.call_args_list]
    assert paths == ["/health", "/", "/api/health", "/-/healthy", "/api/health"]
    assert by_name["backend"]["reachable"] is True
    assert by_name["backend"]["detail"] == "/health"
    assert by_name["prometheus"]["url"] == "http://service"


def test_http_down_state_is_reported():
    repo = _repo()
    with _probes(repo, http_result={"reachable": False, "url": "http://down"}):
        entries = health.get_infrastructure_status(repo)
    by_name = {e["name"]: e for e in entries}
    assert by_name["web"]["reachable"] is False
    assert by_name["web"]["url"] == "http://down"


def test_database_entries_report_ping_results():
    repo = _repo()
    with _probes(repo, mysql=(False, "pool exhausted"), mongo=(True, "ping ok")):
        entries = health.get_infrastructure_status(repo)
    by_name = {e["name"]: e for e in entries}
    assert by_name["mysql"]["reachable"] is False
    assert by_name["mysql"]["detail"] == "pool exhausted"
    assert by_name["mysql"]["kind"] == "database"
    assert by_name["mongo"]["reachable"] is True
    assert by_name["mongo"]["detail"] == "Connected"


@pytest.mark.parametrize("last,expected_reachable", [
    (None, False),
    ((datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(), True),
    ((datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), False),
])
def test_activity_entries_use_log_freshness(last, expected_reachable):
    repo = _repo()
    repo.read_last_activity.return_value = last
    with _probes(repo):
        entries = health.get_infrastructure_status(repo)
    by_name = {e["name"]: e for e in entries}
    assert by_name["cron"]["reachable"] is expected_reachable
    assert by_name["cron"]["lastActivity"] == last
    assert by_name["cron"]["kind"] == "activity"
    assert by_name["scrapper"]["reachable"] is expected_reachable


def test_ollama_entry_carries_server_details_and_errors():
    repo = _repo()
    repo.check_ollama_errors.return_value = [{"event": "ollama.unreachable"}]
    ollama = {"reachable": True, "serverUrl": "http://192.168.1.45:11434", "serverIp": "192.168.1.45", "isLan": True}
    with _probes(repo, ollama=ollama):
        entries = health.get_infrastructure_status(repo)
    ollama_entry = entries[0]
    assert ollama_entry["kind"] == "ollama"
    assert ollama_entry["reachable"] is True
    assert ollama_entry["serverIp"] == "192.168.1.45"
    assert ollama_entry["isLan"] is True
    assert ollama_entry["recentErrors"] == [{"event": "ollama.unreachable"}]
