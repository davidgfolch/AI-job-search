"""Fixtures, patch targets and helpers shared by ollama_client_test and ollama_probe_test."""

import pytest
from unittest.mock import MagicMock

from commonlib.test.ollama_constants import OLLAMA_TEST_URL

# `requests` and `time` are single shared modules: patched here once, both
# ollama_client and ollama_probe see the replacement (they import the same objects).
POST = "requests.post"
GET = "requests.get"
SLEEP = "time.sleep"
CANDIDATES = "commonlib.ollama_probe._candidate_urls"
PROBE = "commonlib.ollama_probe._probe_inference"
AUTO_DISCOVER = "commonlib.network.ollama_resolve.auto_discover_host"
DISCOVERY_ENABLED = "commonlib.ollama_probe.OLLAMA_DISCOVERY_ENABLED"
PROBE_CACHE_SECONDS = "commonlib.ollama_probe.PROBE_CACHE_SECONDS"
FALLBACK_LOG = "ollama.fallback_active"
LOCAL_URL = "http://localhost:11434"
DISCOVERED_HOST = "192.168.1.50"
DISCOVERED_URL = f"http://{DISCOVERED_HOST}:11434"


def _ok(raw="x"):
    m = MagicMock()
    m.json.return_value = {"response": raw}
    m.raise_for_status.return_value = None
    return m


def _down():
    m = MagicMock()
    m.raise_for_status.side_effect = Exception("down")
    return m


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    monkeypatch.setattr(SLEEP, lambda *a, **k: None)


@pytest.fixture(autouse=True)
def clean_fallback_urls(monkeypatch):
    monkeypatch.setattr("commonlib.ollama_probe._logged_fallback_urls", set())


@pytest.fixture(autouse=True)
def no_lan_scan(monkeypatch):
    """The LAN scanner must never reach the real network from the unit suite."""
    monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=None))


@pytest.fixture(autouse=True)
def clear_probe_cache(monkeypatch):
    monkeypatch.setattr("commonlib.ollama_probe._probed_servers", {})


@pytest.fixture(autouse=True)
def clear_last_ollama_server(monkeypatch):
    """The last-known Ollama server is per-process state: reset between tests."""
    monkeypatch.setattr("commonlib.ollama_probe._LAST_OLLAMA_SERVER", {"url": None, "ip": None, "is_lan": False})


@pytest.fixture(autouse=True)
def inference_probe_ok(monkeypatch):
    """A job is only sent after the inference probe passed; the probe itself is covered by TestInferenceProbe."""
    m = MagicMock(return_value=True)
    monkeypatch.setattr(PROBE, m)
    return m


@pytest.fixture
def post(monkeypatch):
    m = MagicMock(return_value=_ok())
    monkeypatch.setattr(POST, m)
    return m


@pytest.fixture
def get(monkeypatch):
    m = MagicMock(return_value=_ok())
    monkeypatch.setattr(GET, m)
    return m


@pytest.fixture
def single(monkeypatch):
    monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_TEST_URL,))
