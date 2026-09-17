import pytest

from commonlib.ollama_config import (
    OLLAMA_HOST_BASE_URL,
    OLLAMA_DOCKER_BASE_URL,
    OLLAMA_HOST_FROM_DOCKER_BASE_URL,
    ollama_candidate_urls,
    ollama_probe_urls,
)


def test_ollama_host_base_url():
    assert OLLAMA_HOST_BASE_URL == "http://localhost:11434"


def test_ollama_docker_base_url():
    assert OLLAMA_DOCKER_BASE_URL == "http://ollama:11434"


def test_ollama_host_from_docker_base_url():
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
        mapping = {
            "AI_ENRICH_OLLAMA_BASE_URL": "http://ollama:11434",
            "AI_ENRICHSKILL_OLLAMA_BASE_URL": "http://ollama:11434",
            "OLLAMA_BASE_URL": None,
        }
        return mapping.get(key, default)
    monkeypatch.setattr("commonlib.ollama_config.getEnv", fake_get_env)
    assert ollama_probe_urls() == ("http://ollama:11434", "http://host.docker.internal:11434", "http://localhost:11434")


def test_ollama_probe_urls_without_module_env(monkeypatch):
    def fake_get_env(key, default=None, required=False):
        return None
    monkeypatch.setattr("commonlib.ollama_config.getEnv", fake_get_env)
    assert ollama_probe_urls() == ("http://host.docker.internal:11434", "http://localhost:11434", "http://ollama:11434")


def test_ollama_probe_urls_deduplicates_shared_servers(monkeypatch):
    def fake_get_env(key, default=None, required=False):
        mapping = {
            "AI_ENRICH_OLLAMA_BASE_URL": "http://localhost:11434",
            "AI_ENRICHSKILL_OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_BASE_URL": None,
        }
        return mapping.get(key, default)
    monkeypatch.setattr("commonlib.ollama_config.getEnv", fake_get_env)
    assert ollama_probe_urls() == ("http://localhost:11434", "http://host.docker.internal:11434", "http://ollama:11434")