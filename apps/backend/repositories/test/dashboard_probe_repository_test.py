from unittest.mock import MagicMock, patch

from repositories.dashboard_probe_repository import DashboardProbeRepository

REPO_MODULE = "repositories.dashboard_probe_repository"


def test_probe_mysql_runs_read_only_query_and_closes_connection():
    conn = MagicMock()
    with patch(f"{REPO_MODULE}.get_read_connection", return_value=conn):
        ok, detail = DashboardProbeRepository().probe_mysql()
    assert ok is True
    assert detail == "SELECT 1 ok"
    conn.cursor.return_value.execute.assert_called_once_with("SELECT 1")
    conn.cursor.return_value.fetchall.assert_called_once_with()
    conn.cursor.return_value.close.assert_called_once()
    conn.consume_results.assert_called_once_with()
    conn.close.assert_called_once()


def test_probe_mysql_close_error_does_not_break_probe():
    conn = MagicMock()
    conn.close.side_effect = RuntimeError("Unread result found")
    with patch(f"{REPO_MODULE}.get_read_connection", return_value=conn):
        ok, detail = DashboardProbeRepository().probe_mysql()
    assert ok is True
    assert detail == "SELECT 1 ok"


def test_probe_mysql_unread_result_is_contained():
    conn = MagicMock()
    conn.cursor.return_value.execute.side_effect = RuntimeError("Unread result found")
    with patch(f"{REPO_MODULE}.get_read_connection", return_value=conn):
        ok, detail = DashboardProbeRepository().probe_mysql()
    assert ok is False
    assert "Unread result found" in detail
    conn.consume_results.assert_called_once_with()
    conn.close.assert_called_once()


def test_probe_mysql_failure_reports_error_and_closes_connection():
    conn = MagicMock()
    conn.cursor.side_effect = RuntimeError("pool exhausted")
    with patch(f"{REPO_MODULE}.get_read_connection", return_value=conn):
        ok, detail = DashboardProbeRepository().probe_mysql()
    assert ok is False
    assert "pool exhausted" in detail
    conn.close.assert_called_once()


def test_probe_mysql_connection_error_is_contained():
    with patch(f"{REPO_MODULE}.get_read_connection", side_effect=ConnectionError("no host")):
        ok, detail = DashboardProbeRepository().probe_mysql()
    assert ok is False
    assert "no host" in detail


def test_probe_mongo_pings_and_closes_client():
    client = MagicMock()
    uri = "mongodb://localhost:27017/"
    with patch(f"{REPO_MODULE}.MongoClient", return_value=client) as ctor:
        ok, detail = DashboardProbeRepository().probe_mongo(uri)
    assert ok is True
    assert detail == "ping ok"
    ctor.assert_called_once_with(uri, serverSelectionTimeoutMS=2000)
    client.admin.command.assert_called_once_with("ping")
    client.close.assert_called_once()


def test_probe_mongo_failure_reports_error_and_closes_client():
    client = MagicMock()
    client.admin.command.side_effect = RuntimeError("server selection timeout")
    with patch(f"{REPO_MODULE}.MongoClient", return_value=client):
        ok, detail = DashboardProbeRepository().probe_mongo("mongodb://localhost:27017/")
    assert ok is False
    assert "server selection timeout" in detail
    client.close.assert_called_once()


def test_probe_mongo_close_error_does_not_break_probe():
    client = MagicMock()
    client.close.side_effect = RuntimeError("client already closed")
    with patch(f"{REPO_MODULE}.MongoClient", return_value=client):
        ok, detail = DashboardProbeRepository().probe_mongo("mongodb://localhost:27017/")
    assert ok is True
    assert detail == "ping ok"


def test_display_url_mongo_hides_credentials():
    url = DashboardProbeRepository.display_url("mongo", "mongodb://user:secret@db.host:27017/")
    assert url == "mongodb://db.host:27017"
    assert "secret" not in url


def test_display_url_mysql_uses_configured_host():
    with patch(f"{REPO_MODULE}.getEnv", return_value="mysql_db"):
        assert DashboardProbeRepository.display_url("mysql", "") == "mysql://mysql_db:3306"
