import pytest
from unittest.mock import patch, MagicMock
import services.dashboard_probe as dashboard_probe


@patch("services.dashboard_probe.get_last_ollama_server")
@patch("services.dashboard_probe.resolve_ollama_url")
@patch("services.dashboard_probe.urllib.request.urlopen")
def test_probe_ollama_reachable_last_known(mock_urlopen, mock_resolve, mock_last):
    """The last-known server IP:port is probed fresh (no cache) and trusted."""
    mock_last.return_value = {
        "url": "http://192.168.1.211:11434",
        "ip": "192.168.1.211",
        "is_lan": True,
    }
    resp = MagicMock()
    resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = resp

    result = dashboard_probe._probe_ollama()

    mock_resolve.assert_not_called()  # last-known answered, no fallback needed
    assert result["reachable"] is True
    assert result["serverUrl"] == "http://192.168.1.211:11434"
    assert result["serverIp"] == "192.168.1.211"
    assert result["isLan"] is True


@patch("services.dashboard_probe.get_last_ollama_server")
@patch("services.dashboard_probe.resolve_ollama_url")
@patch("services.dashboard_probe.urllib.request.urlopen")
def test_probe_ollama_reachable_via_lan_discovery(mock_urlopen, mock_resolve, mock_last):
    """Last-known is down; Ollama on another LAN PC is found by the subnet scan."""
    mock_last.return_value = {
        "url": "http://192.168.1.211:11434",
        "ip": "192.168.1.211",
        "is_lan": True,
    }
    # last-known probe fails
    mock_urlopen.side_effect = OSError("connection refused")
    mock_resolve.return_value = "http://192.168.1.211:11434"

    result = dashboard_probe._probe_ollama()

    mock_resolve.assert_called_once()
    assert result["reachable"] is True
    assert result["serverUrl"] == "http://192.168.1.211:11434"
    assert result["serverIp"] == "192.168.1.211"
    assert result["isLan"] is True


@patch("services.dashboard_probe.get_last_ollama_server")
@patch("services.dashboard_probe.resolve_ollama_url")
@patch("services.dashboard_probe.urllib.request.urlopen")
def test_probe_ollama_unreachable_keeps_last_known(mock_urlopen, mock_resolve, mock_last):
    """Nothing reachable: last-known address is reported as unreachable (not blank)."""
    mock_last.return_value = {
        "url": "http://192.168.1.211:11434",
        "ip": "192.168.1.211",
        "is_lan": True,
    }
    mock_urlopen.side_effect = OSError("connection refused")
    mock_resolve.return_value = None

    result = dashboard_probe._probe_ollama()

    assert result["reachable"] is False
    assert result["serverUrl"] == "http://192.168.1.211:11434"
    assert result["serverIp"] == "192.168.1.211"
    assert result["isLan"] is True


@patch("services.dashboard_probe.get_last_ollama_server")
@patch("services.dashboard_probe.resolve_ollama_url")
@patch("services.dashboard_probe.urllib.request.urlopen")
def test_probe_ollama_no_cache_probes_last_known_every_time(mock_urlopen, mock_resolve, mock_last):
    """No TTL cache: the last-known server is probed fresh on every call."""
    mock_last.return_value = {
        "url": "http://192.168.1.211:11434",
        "ip": "192.168.1.211",
        "is_lan": True,
    }
    resp = MagicMock()
    resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = resp

    dashboard_probe._probe_ollama()
    dashboard_probe._probe_ollama()
    dashboard_probe._probe_ollama()

    # urllib called once per _probe_ollama call (last-known always probed first)
    assert mock_urlopen.call_count == 3
    mock_resolve.assert_not_called()


def test_host_ip_localhost():
    assert dashboard_probe._host_ip("http://localhost:11434") == "127.0.0.1"


def test_host_ip_lan():
    assert dashboard_probe._host_ip("http://192.168.1.45:11434") == "192.168.1.45"


@pytest.mark.parametrize("url,expected", [
    ("http://localhost:11434", False),
    ("http://127.0.0.1:11434", False),
    ("http://host.docker.internal:11434", False),
    ("http://ollama:11434", False),
    ("http://192.168.1.45:11434", True),
])
def test_is_lan_url(url, expected):
    assert dashboard_probe._is_lan_url(url) is expected
