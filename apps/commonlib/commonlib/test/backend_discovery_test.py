from unittest.mock import Mock, patch

import pytest

from commonlib import backend_discovery as sut

ENV_KEYS = (sut.BACKEND_URL_ENV, sut.BACKEND_PORT_ENV, sut.BACKEND_DISCOVERY_ENV)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize("in_docker, expected", [
    (False, ("http://localhost:9000", "http://host.docker.internal:9000", "http://backend:9000")),
    (True, ("http://backend:9000", "http://host.docker.internal:9000", "http://localhost:9000")),
], ids=["host", "docker"])
def test_candidate_urls_follow_topology_and_port(monkeypatch, in_docker, expected):
    monkeypatch.setenv(sut.BACKEND_PORT_ENV, "9000")
    with patch.object(sut.os.path, "exists", return_value=in_docker):
        assert sut.candidate_urls() == expected


def test_configured_url_pins_candidates(monkeypatch):
    monkeypatch.setenv(sut.BACKEND_URL_ENV, "http://main-box:8000/")
    assert sut.candidate_urls() == ("http://main-box:8000",)


def test_configured_url_skips_probes(monkeypatch):
    monkeypatch.setenv(sut.BACKEND_URL_ENV, "http://main-box:8000")
    with patch.object(sut, "verify_backend") as verify:
        assert sut.get_backend_url() == "http://main-box:8000"
    verify.assert_not_called()


def test_probes_candidates_in_order(monkeypatch):
    with patch.object(sut, "verify_backend", side_effect=[False, True]) as verify:
        assert sut.get_backend_url() == "http://host.docker.internal:8000"
    assert [call.args[0] for call in verify.call_args_list] == [
        "http://localhost:8000", "http://host.docker.internal:8000"]


def test_lan_discovery_is_the_last_resort(monkeypatch):
    monkeypatch.setenv(sut.BACKEND_DISCOVERY_ENV, "True")
    monkeypatch.setenv(sut.BACKEND_PORT_ENV, "9000")
    with patch.object(sut, "verify_backend", return_value=False), patch.object(sut, "_discover_host", return_value="192.168.1.20") as discover:
        assert sut.get_backend_url() == "http://192.168.1.20:9000"
    discover.assert_called_once_with(9000, sut.PROBE_TIMEOUT)


def test_discovery_can_be_disabled(monkeypatch):
    with patch.object(sut, "verify_backend", return_value=False), patch.object(sut, "_discover_host") as discover:
        assert sut.get_backend_url() is None
    discover.assert_not_called()


@pytest.mark.parametrize("response, expected", [
    (Mock(ok=True), True),
    (Mock(ok=False), False),
    (OSError("offline"), False),
], ids=["healthy", "unhealthy", "error"])
def test_verify_backend(response, expected):
    with patch.object(sut.requests, "get", side_effect=response if isinstance(response, Exception) else None, return_value=response if not isinstance(response, Exception) else None) as get:
        assert sut.verify_backend("http://backend:8000/") is expected
    assert get.call_args.args[0] == "http://backend:8000/health"
