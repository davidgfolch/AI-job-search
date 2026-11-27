import pytest
from unittest.mock import MagicMock

from commonlib import ollama_server_registry
from commonlib.ollama_server_registry import (
    _discover_ollama_lan_url, _host_ip, _is_lan_url, _record_ollama_server, get_last_ollama_server,
)
from commonlib.test.ollama_fixtures import (  # noqa: F401 - the autouse fixtures register by being imported here
    AUTO_DISCOVER, DISCOVERED_HOST, DISCOVERED_URL, clear_last_ollama_server, no_lan_scan,
)


class TestHostIp:

    @pytest.mark.parametrize("url, expected", [
        ("http://localhost:11434", "127.0.0.1"),
        ("http://no-such-host.invalid:11434", "no-such-host.invalid"),
    ], ids=["resolvable", "unresolvable"])
    def test_host_identity(self, url, expected):
        assert _host_ip(url) == expected


class TestLanScope:

    @pytest.mark.parametrize("url, expected", [
        ("http://localhost:11434", False),
        ("http://host.docker.internal:11434", False),
        ("http://192.168.1.50:11434", True),
    ], ids=["localhost", "docker-host", "lan-ip"])
    def test_is_lan_url(self, url, expected):
        assert _is_lan_url(url) is expected


class TestLearnedServer:

    def test_starts_with_no_server(self):
        assert get_last_ollama_server()["url"] is None

    def test_records_the_server_with_its_ip_and_scope(self):
        log = MagicMock()
        _record_ollama_server(DISCOVERED_URL, log)
        assert get_last_ollama_server() == {"url": DISCOVERED_URL, "ip": DISCOVERED_HOST, "is_lan": True}
        assert log.info.call_args[0][0] == "ollama.server_learned"

    def test_callers_cannot_mutate_the_learned_server(self):
        """Every module reads a copy, so no caller can re-point the others' server."""
        log = MagicMock()
        _record_ollama_server(DISCOVERED_URL, log)
        get_last_ollama_server().update({"url": "http://elsewhere:11434"})
        assert get_last_ollama_server()["url"] == DISCOVERED_URL


class TestLanDiscovery:

    def test_returns_the_discovered_url(self, monkeypatch):
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=DISCOVERED_HOST))
        assert _discover_ollama_lan_url(MagicMock()) == DISCOVERED_URL

    def test_returns_none_when_nothing_answers(self, monkeypatch):
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=None))
        assert _discover_ollama_lan_url(MagicMock()) is None

    def test_disabled_discovery_does_not_scan(self, monkeypatch):
        scan = MagicMock(return_value=DISCOVERED_HOST)
        monkeypatch.setattr(AUTO_DISCOVER, scan)
        monkeypatch.setattr(ollama_server_registry, "OLLAMA_DISCOVERY_ENABLED", False)
        assert _discover_ollama_lan_url(MagicMock()) is None
        scan.assert_not_called()

    def test_scan_failure_is_logged_and_ignored(self, monkeypatch):
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(side_effect=RuntimeError("scan blew up")))
        log = MagicMock()
        assert _discover_ollama_lan_url(log) is None
        assert log.warning.call_args[0][0] == "ollama.discovery_failed"
