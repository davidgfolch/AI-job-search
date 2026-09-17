import pytest
import requests
from unittest.mock import MagicMock

from commonlib.test.ollama_constants import OLLAMA_TEST_URL, OLLAMA_DOCKER_TEST_URL
from commonlib.ollama_client import ping_ollama, query_ollama, resolve_ollama_url
from commonlib.ollama_config import OLLAMA_HOST_FROM_DOCKER_BASE_URL

POST = "commonlib.ollama_client.requests.post"
GET = "commonlib.ollama_client.requests.get"
CANDIDATES = "commonlib.ollama_client._candidate_urls"
FALLBACK_LOG = "ollama.fallback_active"


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

    def test_success(self, post, single):
        post.return_value = _ok('{"key": "value"}')
        assert query_ollama("test prompt") == '{"key": "value"}'
        post.assert_called_once()

    def test_no_json_mode(self, post, single):
        post.return_value = _ok("plain text")
        assert query_ollama("prompt", json_mode=False) == "plain text"
        assert "format" not in post.call_args[1]["json"]

    def test_json_mode_adds_format(self, post, single):
        query_ollama("prompt", json_mode=True)
        assert post.call_args[1]["json"]["format"] == "json"

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
