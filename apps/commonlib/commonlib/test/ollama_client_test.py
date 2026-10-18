import pytest
import requests
from unittest.mock import MagicMock

from commonlib.ollama_client import OllamaResponse, query_ollama
from commonlib.ollama_config import OLLAMA_HOST_FROM_DOCKER_BASE_URL
from commonlib.test.ollama_constants import OLLAMA_DOCKER_TEST_URL, OLLAMA_TEST_URL
from commonlib.test.ollama_fixtures import (  # noqa: F401 - the autouse fixtures register by being imported here
    AUTO_DISCOVER, CANDIDATES, DISCOVERY_ENABLED, DISCOVERED_HOST, DISCOVERED_URL, LOCAL_URL, POST, _down, _ok,
    clean_fallback_urls, clear_probe_cache, inference_probe_ok, no_lan_scan, no_retry_sleep, post, single,
)

SCHEMA = {"type": "object"}


class TestQueryOllama:

    @pytest.mark.parametrize("body, expected", [
        ({"response": '{"key": "value"}'}, '{"key": "value"}'),
        ({}, ""),
    ], ids=["json-body", "empty-body"])
    def test_returns_the_response_field(self, post, single, inference_probe_ok, body, expected):
        post.return_value.json.return_value = body
        assert query_ollama("test prompt") == expected
        post.assert_called_once()
        assert inference_probe_ok.call_args[0][:2] == (OLLAMA_TEST_URL, "qwen2.5:3b")

    @pytest.mark.parametrize("kwargs, expected_format", [
        ({}, "json"),
        ({"json_mode": False}, None),
        ({"json_mode": True, "response_schema": SCHEMA}, SCHEMA),
    ], ids=["default-json", "no-json-mode", "schema"])
    def test_payload_format_follows_json_mode(self, post, single, kwargs, expected_format):
        assert query_ollama("prompt", **kwargs) == "x"
        assert post.call_args[1]["json"].get("format") == expected_format

    def test_schema_and_metadata_are_returned(self, post, single):
        post.return_value.json.return_value = {
            "response": '{"ok": true}',
            "model": "qwen2.5:3b",
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 12,
            "eval_count": 3,
        }
        response = query_ollama("prompt", response_schema=SCHEMA, return_metadata=True)
        assert isinstance(response, OllamaResponse)
        assert response.text == '{"ok": true}'
        assert response.done_reason == "stop"
        assert response.prompt_eval_count == 12
        assert response.eval_count == 3

    @pytest.mark.parametrize("failure, candidates, expected_calls", [
        ("generic error", (OLLAMA_TEST_URL,), 3),
        ("non-dict body", (OLLAMA_TEST_URL,), 3),
        ("http error", (OLLAMA_TEST_URL, OLLAMA_DOCKER_TEST_URL, "http://x:11434"), 9),
        ("read timeout", (OLLAMA_TEST_URL, OLLAMA_DOCKER_TEST_URL), 2),
    ], ids=["generic-error", "non-dict-body", "http-error", "read-timeout"])
    def test_failures_are_retried_then_give_up(self, monkeypatch, failure, candidates, expected_calls):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: candidates)
        m = MagicMock()
        if failure == "generic error":
            m.side_effect = Exception("fail")
        elif failure == "non-dict body":
            m.return_value.json.return_value = ["not", "an", "object"]
        elif failure == "http error":
            m.return_value = _down()
        else:  # a read timeout drops the candidate without any retry
            m.side_effect = requests.exceptions.ReadTimeout("timeout")
        monkeypatch.setattr(POST, m)
        assert query_ollama("prompt") is None
        assert m.call_count == expected_calls

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

    def test_no_job_sent_when_no_candidate_can_infer(self, post, inference_probe_ok, single):
        inference_probe_ok.return_value = False
        assert query_ollama("prompt") is None
        post.assert_not_called()


class TestQueryLanDiscovery:

    @pytest.mark.parametrize("primary_url, candidates, enabled, expected_text, side_effects", [
        (None, (OLLAMA_TEST_URL,), True, "lan result", [Exception("fail")] * 3 + [_ok("lan result")]),
        (LOCAL_URL, (LOCAL_URL,), True, None, [Exception("fail")] * 3),
        (None, (OLLAMA_TEST_URL,), False, None, [Exception("fail")] * 3),
        ("auto", (), True, "lan result", [_ok("lan result")]),
        ("auto", (), True, None, [Exception("fail")] * 3),
    ], ids=["candidates-fail", "already-tried", "discovery-disabled", "auto-spec", "auto-spec-unreachable"])
    def test_query_falls_back_to_lan_discovery(self, post, monkeypatch, primary_url, candidates, enabled, expected_text, side_effects):
        monkeypatch.setattr(CANDIDATES, lambda *a, **k: candidates)
        monkeypatch.setattr(DISCOVERY_ENABLED, enabled)
        scan = MagicMock(return_value=DISCOVERED_HOST)
        monkeypatch.setattr(AUTO_DISCOVER, scan)
        post.side_effect = side_effects
        assert query_ollama("prompt", primary_url=primary_url) == expected_text
        assert scan.called is enabled
        if expected_text is not None:
            assert post.call_args[0][0] == f"{DISCOVERED_URL}/api/generate"
