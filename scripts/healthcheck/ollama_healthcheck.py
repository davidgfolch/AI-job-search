#!/usr/bin/env python
"""Healthcheck script for AI-backend-dependent services.
Returns exit code 0 if the live backend (Ollama, cloud provider or in-process HuggingFace) is usable, 1 otherwise.
Used by Docker HEALTHCHECK to mark container as unhealthy when the backend is down.

The last discovered host is probed first: the workers resolve Ollama at runtime
(`resolve_ollama_url`), so a healthcheck limited to the static fallback
candidates would report a working worker as unhealthy whenever the server lives
on the LAN. The cached host is used even when its TTL expired — idle workers do
not refresh it, and the HTTP probe verifies it anyway. No scan is started here."""
import sys
import requests

from commonlib.cloud_llm import is_cloud, ping as ping_cloud
from commonlib.environmentUtil import getEnv
from commonlib.envFileUtil import getEnvFile
from commonlib.network.discovery_cache import read_entry
from commonlib.network.ollama_discovery import DEFAULT_OLLAMA_PORT
from commonlib.ollama_config import ollama_probe_urls

MODULE_BACKEND_ENVS = {
    "aienrich": "AI_ENRICH_LLM_BACKEND",
    "aienrichskill": "AI_ENRICHSKILL_BACKEND",
}


def discovered_ollama_url() -> str | None:
    """The last discovered Ollama host, if any (the HTTP probe checks it)."""
    entry = read_entry("ollama", ignore_ttl=True) or {}
    host = entry.get("host")
    return f"http://{host}:{DEFAULT_OLLAMA_PORT}" if host else None


def check_ollama() -> bool:
    timeout = int(getEnv("HEALTHCHECK_TIMEOUT", "5"))
    discovered = discovered_ollama_url()
    for url in ([discovered] if discovered else []) + list(ollama_probe_urls()):
        try:
            resp = requests.get(f"{url.rstrip('/')}/api/tags", timeout=timeout)
            resp.raise_for_status()
            return True
        except Exception:
            continue
    return False


def check_cloud(provider: str) -> bool:
    """Cloud providers expose an OpenAI-compatible /models endpoint."""
    timeout = int(getEnv("HEALTHCHECK_TIMEOUT", "5"))
    base_url = getEnv("AI_ENRICH_OPENROUTER_BASE_URL", "") if provider == "openrouter" else ""
    return ping_cloud(provider, timeout=timeout, base_url=base_url or None)


def check_backend() -> bool:
    """Follow the live provider from .env; local huggingface runs in-process."""
    key = MODULE_BACKEND_ENVS.get(getEnv("HEALTHCHECK_MODULE", ""))
    backend = getEnvFile(key, "ollama") if key else getEnv("HEALTHCHECK_BACKEND", "ollama")
    if backend == "huggingface":
        return True
    if is_cloud(backend):
        return check_cloud(backend)
    return check_ollama()


if __name__ == "__main__":
    sys.exit(0 if check_backend() else 1)
