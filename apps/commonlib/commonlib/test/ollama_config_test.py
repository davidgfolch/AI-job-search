from commonlib.ollama_config import OLLAMA_DEFAULT_BASE_URL, OLLAMA_DOCKER_BASE_URL


def test_ollama_default_base_url():
    assert OLLAMA_DEFAULT_BASE_URL == "http://localhost:11434"


def test_ollama_docker_base_url():
    assert OLLAMA_DOCKER_BASE_URL == "http://ollama:11434"