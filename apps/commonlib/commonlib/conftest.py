"""Shared isolation for the commonlib unit suite."""
import pytest


@pytest.fixture(autouse=True)
def isolated_discovery_cache(tmp_path, monkeypatch):
    """Never read or write the real `data/discovery` cache from a unit test.

    Every test gets its own cache file, so a stale entry written by one test can
    never answer a discovery call made by another.
    """
    monkeypatch.setenv("COMMONLIB_DISCOVERY_CACHE", str(tmp_path / "discovery" / "cache.json"))


@pytest.fixture(autouse=True)
def isolated_ollama_activity(tmp_path, monkeypatch):
    """Keep the inference-slot marker and lock files out of the real `data/metrics` directory."""
    monkeypatch.setenv("AI_ENRICH_OLLAMA_ACTIVITY_DIR", str(tmp_path / "ollama_activity"))
