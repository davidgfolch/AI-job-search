import os
from unittest.mock import patch
import pytest


class TestCheckBackendAvailable:
    def test_exits_when_no_server_was_ever_resolved(self, monkeypatch):
        from aiEnrich import ollama_backend
        monkeypatch.setattr(ollama_backend, "_resolved_ollama_url", None)
        monkeypatch.setattr(ollama_backend, "_ollama_server_known", False)
        monkeypatch.setattr(ollama_backend, "ollama_consecutive_failures", 0)
        monkeypatch.setattr(ollama_backend, "get_backend", lambda: "ollama")
        monkeypatch.setattr(ollama_backend, "get_max_ollama_failures", lambda: 3)
        monkeypatch.setattr(ollama_backend, "ping_backend", lambda: False)
        with patch.object(ollama_backend, "logger") as mock_logger:
            assert ollama_backend._check_backend_available() is False
            assert ollama_backend._check_backend_available() is False
            with pytest.raises(SystemExit):
                ollama_backend._check_backend_available()
        mock_logger.critical.assert_called_once_with("ai.exit_threshold_reached", consecutive_failures=3)

    def test_keeps_retrying_when_the_resolved_server_is_unreachable(self, monkeypatch):
        """A sleeping LAN host must not stop the pipeline: once the server was reached,
        failures keep the cycle returning -1 so the pipeline waits until it answers again."""
        from aiEnrich import ollama_backend
        monkeypatch.setattr(ollama_backend, "_resolved_ollama_url", None)
        monkeypatch.setattr(ollama_backend, "_ollama_server_known", True)
        monkeypatch.setattr(ollama_backend, "ollama_consecutive_failures", 0)
        monkeypatch.setattr(ollama_backend, "get_backend", lambda: "ollama")
        monkeypatch.setattr(ollama_backend, "get_max_ollama_failures", lambda: 3)
        monkeypatch.setattr(ollama_backend, "ping_backend", lambda: False)
        assert [ollama_backend._check_backend_available() for _ in range(5)] == [False] * 5
        assert ollama_backend.ollama_consecutive_failures == 5
        monkeypatch.setattr(ollama_backend, "ping_backend", lambda: True)
        assert ollama_backend._check_backend_available() is True
        assert ollama_backend.ollama_consecutive_failures == 0


class TestPingBackend:
    def test_routes_to_ollama(self, monkeypatch):
        os.environ["AI_ENRICH_BACKEND"] = "ollama"
        from aiEnrich import ollama_backend
        monkeypatch.setattr(ollama_backend, "_resolved_ollama_url", None)
        monkeypatch.setattr(ollama_backend, "_ollama_server_known", False)
        with patch.object(ollama_backend, "resolve_ollama_url", return_value="http://host:11434") as mock_resolve, \
             patch.object(ollama_backend, "ping_openrouter") as mock_ping_or:
            assert ollama_backend.ping_backend() is True
        mock_resolve.assert_called_once()
        mock_ping_or.assert_not_called()
        assert ollama_backend._ollama_server_known is True

    def test_rediscovers_when_cached_server_stops_answering(self, monkeypatch):
        """A sleeping LAN host may come back on another address: the cached URL must be
        dropped and resolved again instead of being pinged forever."""
        from aiEnrich import ollama_backend
        monkeypatch.setattr(ollama_backend, "_resolved_ollama_url", "http://192.168.1.50:11434")
        monkeypatch.setattr(ollama_backend, "_ollama_server_known", True)
        with patch.object(ollama_backend, "get_backend", return_value="ollama"), \
             patch.object(ollama_backend, "_ping_url", return_value=False), \
             patch.object(ollama_backend, "resolve_ollama_url", return_value="http://192.168.1.77:11434") as mock_resolve, \
             patch.object(ollama_backend, "logger"):
            assert ollama_backend.ping_backend() is True
        mock_resolve.assert_called_once()
        assert ollama_backend._resolved_ollama_url == "http://192.168.1.77:11434"
        assert ollama_backend._ollama_server_known is True

    def test_stays_unreachable_when_rediscovery_finds_nothing(self, monkeypatch):
        from aiEnrich import ollama_backend
        monkeypatch.setattr(ollama_backend, "_resolved_ollama_url", "http://192.168.1.50:11434")
        monkeypatch.setattr(ollama_backend, "_ollama_server_known", True)
        with patch.object(ollama_backend, "get_backend", return_value="ollama"), \
             patch.object(ollama_backend, "_ping_url", return_value=False), \
             patch.object(ollama_backend, "resolve_ollama_url", return_value=None), \
             patch.object(ollama_backend, "logger"):
            assert ollama_backend.ping_backend() is False
        assert ollama_backend._resolved_ollama_url is None
        assert ollama_backend._ollama_server_known is True

    def test_routes_to_openrouter(self):
        os.environ["AI_ENRICH_BACKEND"] = "openrouter"
        from aiEnrich import ollama_backend
        with patch.object(ollama_backend, "resolve_ollama_url", return_value=None) as mock_resolve, \
             patch.object(ollama_backend, "ping_openrouter", return_value=True) as mock_ping_or:
            assert ollama_backend.ping_backend() is True
        mock_ping_or.assert_called_once()
        mock_resolve.assert_not_called()
