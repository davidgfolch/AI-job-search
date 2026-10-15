import pytest
import requests
from unittest.mock import MagicMock

from commonlib.test.ollama_constants import OLLAMA_TEST_URL, OLLAMA_DOCKER_TEST_URL
from commonlib.ollama_client import (
    INFERENCE_PROBE_TIMEOUT, OllamaResponse, PROBE_TIMEOUT, _host_ip, _probe_inference,
    ping_ollama, query_ollama, resolve_ollama_url,
)
from commonlib.ollama_config import OLLAMA_HOST_FROM_DOCKER_BASE_URL

POST = "commonlib.ollama_client.requests.post"
GET = "commonlib.ollama_client.requests.get"
CANDIDATES = "commonlib.ollama_client._candidate_urls"
PROBE = "commonlib.ollama_client._probe_inference"
AUTO_DISCOVER = "commonlib.network.ollama_discovery.auto_discover_host"
DISCOVERY_ENABLED = "commonlib.ollama_client.OLLAMA_DISCOVERY_ENABLED"
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
    monkeypatch.setattr("commonlib.ollama_client.time.sleep", lambda *a, **k: None)


@pytest.fixture(autouse=True)
def clean_fallback_urls(monkeypatch):
    monkeypatch.setattr("commonlib.ollama_client._logged_fallback_urls", set())


@pytest.fixture(autouse=True)
def no_lan_scan(monkeypatch):
    """The LAN scanner must never reach the real network from the unit suite."""
    monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=None))


@pytest.fixture(autouse=True)
def clear_probe_cache(monkeypatch):
    monkeypatch.setattr("commonlib.ollama_client._probed_servers", {})


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


class TestQueryOllama:

    def test_success(self, post, single, inference_probe_ok):
        post.return_value = _ok('{"key": "value"}')
        assert query_ollama("test prompt") == '{"key": "value"}'
        post.assert_called_once()
        assert inference_probe_ok.call_args[0][:2] == (OLLAMA_TEST_URL, "qwen2.5:3b")

    def test_no_json_mode(self, post, single):
        post.return_value = _ok("plain text")
        assert query_ollama("prompt", json_mode=False) == "plain text"
        assert "format" not in post.call_args[1]["json"]

    def test_json_mode_adds_format(self, post, single):
        query_ollama("prompt", json_mode=True)
        assert post.call_args[1]["json"]["format"] == "json"

    def test_schema_and_metadata_are_returned(self, post, single):
        post.return_value.json.return_value = {
            "response": '{"ok": true}',
            "model": "qwen2.5:3b",
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 12,
            "eval_count": 3,
        }
        schema = {"type": "object"}
        response = query_ollama("prompt", response_schema=schema, return_metadata=True)
        assert post.call_args[1]["json"]["format"] == schema
        assert isinstance(response, OllamaResponse)
        assert response.text == '{"ok": true}'
        assert response.done_reason == "stop"
        assert response.prompt_eval_count == 12
        assert response.eval_count == 3

    def test_empty_response_field(self, post, single):
        post.return_value.json.return_value = {}
        assert query_ollama("prompt") == ""

    def test_all_failures_return_none(self, post, single):
        post.side_effect = Exception("fail")
        assert query_ollama("prompt") is None
        assert post.call_count == 3

    def test_read_timeout_no_retry(self, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_TEST_URL, OLLAMA_DOCKER_TEST_URL))
        m = MagicMock(side_effect=requests.exceptions.ReadTimeout("timeout"))
        monkeypatch.setattr(POST, m)
        assert query_ollama("prompt") is None
        assert m.call_count == 2

    def test_succeeds_on_second_retry(self, post, single):
        post.side_effect = [Exception("fail"), _ok("ok")]
        assert query_ollama("prompt") == "ok"
        assert post.call_count == 2

    def test_custom_parameters(self, post, single):
        query_ollama("prompt", model="ollama/custom-model", primary_url="http://custom:11434", timeout=30)
        assert post.call_args[1]["json"]["model"] == "custom-model"
        assert post.call_args[1]["timeout"] == 30

    def test_trailing_slash_stripped(self, post, single):
        query_ollama("prompt", primary_url=f"{OLLAMA_TEST_URL}/")
        assert post.call_args[0][0] == f"{OLLAMA_TEST_URL}/api/generate"

    def test_raise_for_status_triggers_retry(self, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_TEST_URL, OLLAMA_DOCKER_TEST_URL, "http://x:11434"))
        m = MagicMock(return_value=_down())
        monkeypatch.setattr(POST, m)
        assert query_ollama("prompt") is None
        assert m.call_count == 9

    def test_falls_back_to_next_candidate(self, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_DOCKER_TEST_URL, OLLAMA_HOST_FROM_DOCKER_BASE_URL))
        m = MagicMock(side_effect=[_down(), _down(), _down(), _ok("host result")])
        monkeypatch.setattr(POST, m)
        assert query_ollama("prompt", primary_url=OLLAMA_DOCKER_TEST_URL) == "host result"
        assert m.call_count == 4
        assert m.call_args[0][0] == f"{OLLAMA_HOST_FROM_DOCKER_BASE_URL}/api/generate"

    def test_candidate_skipped_when_its_probe_fails(self, post, inference_probe_ok, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_DOCKER_TEST_URL, OLLAMA_TEST_URL))
        inference_probe_ok.side_effect = [False, True]
        assert query_ollama("prompt") == "x"
        assert post.call_count == 1
        assert post.call_args[0][0] == f"{OLLAMA_TEST_URL}/api/generate"

    def test_non_dict_response_retries_then_fails(self, post, single):
        post.return_value = _ok()
        post.return_value.json.return_value = ["not", "an", "object"]
        assert query_ollama("prompt") is None
        assert post.call_count == 3

    def test_no_job_sent_when_no_candidate_can_infer(self, post, inference_probe_ok, single):
        inference_probe_ok.return_value = False
        assert query_ollama("prompt") is None
        post.assert_not_called()


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

    def test_probe_reuses_the_job_num_ctx(self, post, single, inference_probe_ok):
        query_ollama("prompt")
        job_options = post.call_args[1]["json"]["options"]
        probed_options = inference_probe_ok.call_args[0][2]
        assert probed_options["num_ctx"] == job_options["num_ctx"]
        assert probed_options["repeat_penalty"] == job_options["repeat_penalty"]

    def test_fails_and_warns_when_the_runner_is_stuck(self, post):
        post.side_effect = requests.exceptions.ReadTimeout("stuck")
        log = MagicMock()
        assert _probe_inference(OLLAMA_TEST_URL, "qwen2.5:3b", {"num_ctx": 16384}, log) is False
        assert log.warning.call_args[0][0] == "ollama.inference_probe_failed"
        assert log.warning.call_args[1]["timeout"] == INFERENCE_PROBE_TIMEOUT

    def test_fails_on_connection_error(self, post):
        post.side_effect = Exception("connection refused")
        assert _probe_inference(OLLAMA_TEST_URL, "qwen2.5:3b", None, MagicMock()) is False

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
        monkeypatch.setattr("commonlib.ollama_client.PROBE_CACHE_SECONDS", 0)
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

    def test_success(self, get, single):
        assert ping_ollama() is True
        get.assert_called_once_with(f"{OLLAMA_TEST_URL}/api/tags", timeout=5)

    def test_failure(self, get, single):
        get.side_effect = Exception("Connection refused")
        assert ping_ollama(timeout=2) is False

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

    def test_returns_candidate(self, get, single):
        assert resolve_ollama_url() == OLLAMA_TEST_URL
        get.assert_called_once_with(f"{OLLAMA_TEST_URL}/api/tags", timeout=5)

    def test_none_when_all_fail(self, get):
        get.side_effect = Exception("down")
        assert resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL, timeout=2) is None

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

    def test_resolves_hostname_to_ip(self):
        assert _host_ip("http://localhost:11434") == "127.0.0.1"

    def test_falls_back_to_the_hostname_when_unresolvable(self):
        assert _host_ip("http://no-such-host.invalid:11434") == "no-such-host.invalid"


class TestLanDiscoveryFallback:

    def test_resolve_uses_discovered_host(self, get, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (OLLAMA_DOCKER_TEST_URL,))
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=DISCOVERED_HOST))
        get.side_effect = Exception("down")
        assert resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL) == DISCOVERED_URL

    def test_resolve_skips_discovered_host_already_probed(self, get, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (LOCAL_URL,))
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value="127.0.0.1"))
        get.side_effect = Exception("down")
        assert resolve_ollama_url(primary_url=LOCAL_URL) is None

    def test_resolve_skips_discovery_when_disabled(self, get, monkeypatch):
        monkeypatch.setattr(DISCOVERY_ENABLED, False)
        scan = MagicMock(return_value=DISCOVERED_HOST)
        monkeypatch.setattr(AUTO_DISCOVER, scan)
        get.side_effect = Exception("down")
        assert resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL) is None
        scan.assert_not_called()

    def test_query_uses_discovered_host_when_candidates_fail(self, post, single, monkeypatch):
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=DISCOVERED_HOST))
        post.side_effect = [Exception("fail")] * 3 + [_ok("lan result")]
        assert query_ollama("prompt") == "lan result"
        assert post.call_args[0][0] == f"{DISCOVERED_URL}/api/generate"

    def test_query_skips_discovered_host_already_tried(self, post, monkeypatch):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: (LOCAL_URL,))
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value="127.0.0.1"))
        post.side_effect = Exception("fail")
        assert query_ollama("prompt") is None
        assert post.call_count == 3

    def test_query_skips_discovery_when_disabled(self, post, single, monkeypatch, inference_probe_ok):
        monkeypatch.setattr(DISCOVERY_ENABLED, False)
        scan = MagicMock(return_value=DISCOVERED_HOST)
        monkeypatch.setattr(AUTO_DISCOVER, scan)
        inference_probe_ok.return_value = False
        assert query_ollama("prompt") is None
        scan.assert_not_called()

    def test_auto_spec_resolves_discovered_host(self, get, monkeypatch):
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=DISCOVERED_HOST))
        assert resolve_ollama_url(primary_url="auto") == DISCOVERED_URL

    def test_auto_spec_unreachable(self, get):
        assert resolve_ollama_url(primary_url="discover") is None

    def test_auto_spec_queried_without_configured_candidates(self, post, monkeypatch):
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(return_value=DISCOVERED_HOST))
        assert query_ollama("prompt", primary_url="auto") == "x"
        assert post.call_args[0][0] == f"{DISCOVERED_URL}/api/generate"

    def test_discovery_scan_failure_is_swallowed(self, get, monkeypatch):
        monkeypatch.setattr(AUTO_DISCOVER, MagicMock(side_effect=Exception("scan blew up")))
        get.side_effect = Exception("down")
        assert resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL) is None
