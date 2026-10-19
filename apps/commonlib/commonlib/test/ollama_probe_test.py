import pytest
import requests
from unittest.mock import MagicMock

from commonlib.ollama_client import query_ollama
from commonlib.ollama_config import OLLAMA_HOST_FROM_DOCKER_BASE_URL
from commonlib.ollama_probe import INFERENCE_PROBE_TIMEOUT, _host_ip, _probe_inference, ping_ollama, resolve_ollama_url
from commonlib.test.ollama_constants import OLLAMA_DOCKER_TEST_URL, OLLAMA_TEST_URL
from commonlib.test.ollama_fixtures import (  # noqa: F401 - the autouse fixtures register by being imported here
    AUTO_DISCOVER, CANDIDATES, DISCOVERY_ENABLED, DISCOVERED_HOST, DISCOVERED_URL, FALLBACK_LOG, LOCAL_URL, POST,
    PROBE_CACHE_SECONDS, _ok, clean_fallback_urls, clear_last_ollama_server, clear_probe_cache, get,
    inference_probe_ok, no_lan_scan, no_retry_sleep, post, single,
)


class TestInferenceProbe:

    def test_passes_when_the_server_answers(self, post):
        log = MagicMock()
        assert _probe_inference(OLLAMA_TEST_URL, "qwen2.5:3b", {"num_ctx": 16384}, log) is True
        assert post.call_args[0][0] == f"{OLLAMA_TEST_URL}/api/generate"
        assert post.call_args[1]["timeout"] == INFERENCE_PROBE_TIMEOUT
        assert post.call_args[1]["json"]["model"] == "qwen2.5:3b"
        assert post.call_args[1]["json"]["options"] == {"num_ctx": 16384, "num_predict": 1}
        assert post.call_args[1]["json"]["stream"] is False
        assert any(c.args[0] == "ollama.inference_probe_ok" for c in log.info.call_args_list)

    @pytest.mark.parametrize("failure, options", [
        (requests.exceptions.ReadTimeout("stuck"), {"num_ctx": 16384}),
        (Exception("connection refused"), None),
    ], ids=["stuck_runner", "connection_error"])
    def test_fails_and_warns(self, post, failure, options):
        post.side_effect = failure
        log = MagicMock()
        assert _probe_inference(OLLAMA_TEST_URL, "qwen2.5:3b", options, log) is False
        assert log.warning.call_args[0][0] == "ollama.inference_probe_failed"
        assert log.warning.call_args[1]["timeout"] == INFERENCE_PROBE_TIMEOUT

    def test_probe_reuses_the_job_num_ctx(self, post, single, inference_probe_ok):
        query_ollama("prompt")
        job_options = post.call_args[1]["json"]["options"]
        probed_options = inference_probe_ok.call_args[0][2]
        assert probed_options["num_ctx"] == job_options["num_ctx"]
        assert probed_options["repeat_penalty"] == job_options["repeat_penalty"]

    def test_trailing_slash_stripped(self, post):
        _probe_inference(f"{OLLAMA_TEST_URL}/", "qwen2.5:3b", None, MagicMock())
        assert post.call_args[0][0] == f"{OLLAMA_TEST_URL}/api/generate"


class TestProbeCache:

    def test_server_is_learned_once_for_following_jobs(self, post, single, inference_probe_ok):
        query_ollama("first job")
        query_ollama("second job")
        query_ollama("third job")
        assert inference_probe_ok.call_count == 1
        assert post.call_count == 3

    def test_reprobes_after_the_cache_expires(self, post, single, inference_probe_ok, monkeypatch):
        monkeypatch.setattr(PROBE_CACHE_SECONDS, 0)
        query_ollama("first job")
        query_ollama("second job")
        assert inference_probe_ok.call_count == 2

    def test_a_timed_out_server_is_probed_again_by_the_next_job(self, single, inference_probe_ok, monkeypatch):
        m = MagicMock(return_value=_ok("first"))
        monkeypatch.setattr(POST, m)
        assert query_ollama("first job") == "first"
        m.side_effect = requests.exceptions.ReadTimeout("wedged")
        assert query_ollama("second job") is None
        assert inference_probe_ok.call_count == 1  # still trusted while the job was dispatched
        m.side_effect = None
        m.return_value = _ok("third")
        assert query_ollama("third job") == "third"
        assert inference_probe_ok.call_count == 2  # the timeout dropped it from the cache

    def test_failed_probe_is_not_remembered(self, post, single, inference_probe_ok):
        inference_probe_ok.side_effect = [False, True]
        assert query_ollama("first job") is None
        assert query_ollama("second job") == "x"
        assert inference_probe_ok.call_count == 2
        assert post.call_count == 1


class TestPingOllama:

    @pytest.mark.parametrize("down, timeout, expected", [
        (False, 5, True),
        (True, 2, False),
    ], ids=["reachable", "unreachable"])
    def test_ping_verdict(self, get, single, down, timeout, expected):
        if down:
            get.side_effect = Exception("Connection refused")
        assert ping_ollama(timeout=timeout) is expected
        get.assert_called_once_with(f"{OLLAMA_TEST_URL}/api/tags", timeout=timeout)

    def test_trailing_slash(self, get):
        ping_ollama(primary_url=f"{OLLAMA_TEST_URL}/")
        assert get.call_args[0][0] == f"{OLLAMA_TEST_URL}/api/tags"

    def test_falls_back_to_host(self, get, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_DOCKER_TEST_URL, OLLAMA_HOST_FROM_DOCKER_BASE_URL))
        get.side_effect = [Exception("down"), _ok()]
        assert ping_ollama(primary_url=OLLAMA_DOCKER_TEST_URL) is True
        assert get.call_count == 2
        assert get.call_args[0][0] == f"{OLLAMA_HOST_FROM_DOCKER_BASE_URL}/api/tags"


class TestResolveOllamaUrl:

    @pytest.mark.parametrize("down, expected", [
        (False, OLLAMA_TEST_URL),
        (True, None),
    ], ids=["reachable", "unreachable"])
    def test_resolves_the_first_reachable_candidate(self, get, single, down, expected):
        if down:
            get.side_effect = Exception("down")
        assert resolve_ollama_url() == expected
        get.assert_called_once_with(f"{OLLAMA_TEST_URL}/api/tags", timeout=5)

    def test_returns_fallback(self, get, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_DOCKER_TEST_URL, OLLAMA_HOST_FROM_DOCKER_BASE_URL))
        get.side_effect = [Exception("down"), _ok()]
        assert resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL) == OLLAMA_HOST_FROM_DOCKER_BASE_URL
        assert get.call_count == 2


class TestFallbackLoggedOnce:

    def test_once(self, get, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_DOCKER_TEST_URL, OLLAMA_HOST_FROM_DOCKER_BASE_URL))
        get.side_effect = [Exception("down"), _ok()]
        log = MagicMock()
        resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL, log=log)
        resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL, log=log)
        assert sum(1 for c in log.info.call_args_list if c.args[0] == FALLBACK_LOG) == 1

    def test_primary_success_no_log(self, get, single):
        log = MagicMock()
        resolve_ollama_url(primary_url=OLLAMA_TEST_URL, log=log)
        assert sum(1 for c in log.info.call_args_list if c.args[0] == FALLBACK_LOG) == 0


class TestHostIp:

    @pytest.mark.parametrize("url, expected", [
        ("http://localhost:11434", "127.0.0.1"),
        ("http://no-such-host.invalid:11434", "no-such-host.invalid"),
    ], ids=["resolvable", "unresolvable"])
    def test_host_identity(self, url, expected):
        assert _host_ip(url) == expected


class TestResolveLanDiscovery:

    @pytest.mark.parametrize("candidates, scan, enabled, expected", [
        ((OLLAMA_DOCKER_TEST_URL,), DISCOVERED_HOST, True, DISCOVERED_URL),
        ((LOCAL_URL,), "127.0.0.1", True, None),
        ((OLLAMA_DOCKER_TEST_URL,), DISCOVERED_HOST, False, None),
        ((OLLAMA_DOCKER_TEST_URL,), RuntimeError("scan blew up"), True, None),
    ], ids=["candidates-fail", "already-tried", "discovery-disabled", "scan-error"])
    def test_resolve_falls_back_to_lan_discovery(self, get, monkeypatch, candidates, scan, enabled, expected):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: candidates)
        monkeypatch.setattr(DISCOVERY_ENABLED, enabled)
        scan_mock = MagicMock(side_effect=scan) if isinstance(scan, Exception) else MagicMock(return_value=scan)
        monkeypatch.setattr(AUTO_DISCOVER, scan_mock)
        get.side_effect = Exception("down")
        assert resolve_ollama_url(primary_url=candidates[0]) == expected
        assert scan_mock.called is enabled

    @pytest.mark.parametrize("primary_url, scan_host, expected", [
        ("auto", DISCOVERED_HOST, DISCOVERED_URL),
        ("discover", None, None),
    ], ids=["auto", "discover"])
    def test_auto_spec_goes_straight_to_discovery(self, get, monkeypatch, primary_url, scan_host, expected):
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=scan_host))
        assert resolve_ollama_url(primary_url=primary_url) == expected
