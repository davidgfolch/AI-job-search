import pytest

from commonlib.ollama_config import (
    OLLAMA_HOST_BASE_URL, OLLAMA_DOCKER_BASE_URL, OLLAMA_HOST_FROM_DOCKER_BASE_URL,
    ollama_candidate_urls, ollama_probe_urls, get_num_ctx, get_repeat_penalty, strip_provider_prefix,
)

URLS = [
    "AI_ENRICH_MAX_NEW_TOKENS", "AI_ENRICHSKILL_MAX_NEW_TOKENS",
    "AI_ENRICH_NUM_CTX", "AI_ENRICHSKILL_NUM_CTX",
    "AI_ENRICH_REPEAT_PENALTY", "AI_ENRICHSKILL_REPEAT_PENALTY",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for env in URLS:
        monkeypatch.delenv(env, raising=False)


def test_host_base_url():
    assert OLLAMA_HOST_BASE_URL == "http://localhost:11434"


def test_docker_base_url():
    assert OLLAMA_DOCKER_BASE_URL == "http://ollama:11434"


def test_host_from_docker_base_url():
    assert OLLAMA_HOST_FROM_DOCKER_BASE_URL == "http://host.docker.internal:11434"


@pytest.mark.parametrize("primary, expected", [
    pytest.param(None, ("http://host.docker.internal:11434", "http://localhost:11434", "http://ollama:11434"), id="no_primary"),
    pytest.param("http://custom:11434", ("http://custom:11434", "http://host.docker.internal:11434", "http://localhost:11434", "http://ollama:11434"), id="custom_primary"),
    pytest.param("http://ollama:11434", ("http://ollama:11434", "http://host.docker.internal:11434", "http://localhost:11434"), id="primary_equals_docker_dedupe"),
    pytest.param("http://localhost:11434", ("http://localhost:11434", "http://host.docker.internal:11434", "http://ollama:11434"), id="primary_equals_host_dedupe"),
])
def test_ollama_candidate_urls(primary, expected):
    assert ollama_candidate_urls(primary) == expected


def test_ollama_probe_urls_with_module_env(monkeypatch):
    def fake_get_env(key, default=None, required=False):
        mapping = {"AI_ENRICH_OLLAMA_BASE_URL": "http://ollama:11434", "AI_ENRICHSKILL_OLLAMA_BASE_URL": "http://ollama:11434", "OLLAMA_BASE_URL": None}
        return mapping.get(key, default)
    monkeypatch.setattr("commonlib.ollama_config.getEnv", fake_get_env)
    assert ollama_probe_urls() == ("http://ollama:11434", "http://host.docker.internal:11434", "http://localhost:11434")


def test_ollama_probe_urls_without_module_env(monkeypatch):
    monkeypatch.setattr("commonlib.ollama_config.getEnv", lambda key, **kw: None)
    assert ollama_probe_urls() == ("http://host.docker.internal:11434", "http://localhost:11434", "http://ollama:11434")


def test_ollama_probe_urls_deduplicates_shared_servers(monkeypatch):
    def fake_get_env(key, default=None, required=False):
        mapping = {"AI_ENRICH_OLLAMA_BASE_URL": "http://localhost:11434", "AI_ENRICHSKILL_OLLAMA_BASE_URL": "http://localhost:11434", "OLLAMA_BASE_URL": None}
        return mapping.get(key, default)
    monkeypatch.setattr("commonlib.ollama_config.getEnv", fake_get_env)
    assert ollama_probe_urls() == ("http://localhost:11434", "http://host.docker.internal:11434", "http://ollama:11434")


@pytest.mark.parametrize("prompt, num_predict, expected", [
    pytest.param("", 50, 2048, id="min_floor"),
    pytest.param("x" * 1000, 2048, 4096, id="buckets_up_to_4k"),
    pytest.param("x" * 6000, 2048, 4096, id="buckets_to_4k"),
    pytest.param("x" * 100000, 4096, 32768, id="capped_at_max"),
])
def test_num_ctx_bucketing(prompt, num_predict, expected):
    assert get_num_ctx(prompt, num_predict) == expected


@pytest.mark.parametrize("env_name", ["AI_ENRICH_NUM_CTX", "AI_ENRICHSKILL_NUM_CTX"])
def test_num_ctx_env_override(monkeypatch, env_name):
    monkeypatch.setenv(env_name, "8192")
    assert get_num_ctx("x" * 10, 50) == 8192


def test_num_ctx_env_override_capped(monkeypatch):
    monkeypatch.setenv("AI_ENRICH_NUM_CTX", "128000")
    assert get_num_ctx("x", 50) == 32768


@pytest.mark.parametrize("env_name", ["AI_ENRICH_REPEAT_PENALTY", "AI_ENRICHSKILL_REPEAT_PENALTY"])
def test_repeat_penalty_env_override(monkeypatch, env_name):
    monkeypatch.setenv(env_name, "1.5")
    assert get_repeat_penalty() == 1.5


def test_repeat_penalty_default():
    assert get_repeat_penalty() == 1.3


@pytest.mark.parametrize("model, expected", [
    pytest.param("ollama/qwen2.5:3b", "qwen2.5:3b", id="strips_ollama"),
    pytest.param("openai/gpt-4", "gpt-4", id="strips_any"),
    pytest.param("qwen2.5:3b", "qwen2.5:3b", id="no_prefix"),
])
def test_strip_provider_prefix(model, expected):
    assert strip_provider_prefix(model) == expected
