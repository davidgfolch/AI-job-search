#!/usr/bin/env python
"""Healthcheck script for AI-backend-dependent services.
Returns exit code 0 if the configured backend (Ollama or OpenRouter) is reachable, 1 otherwise.
Used by Docker HEALTHCHECK to mark container as unhealthy when the backend is down.

The last discovered host is probed first: the workers resolve Ollama at runtime
(`resolve_ollama_url`), so a healthcheck limited to the static fallback
candidates would report a working worker as unhealthy whenever the server lives
on the LAN. The cached host is used even when its TTL expired — idle workers do
not refresh it, and the HTTP probe verifies it anyway. No scan is started here."""
import sys
import requests

from commonlib.environmentUtil import getEnv
from commonlib.network.discovery_cache import read_entry
from commonlib.network.ollama_discovery import DEFAULT_OLLAMA_PORT
from commonlib.ollama_config import ollama_probe_urls

OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


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


def check_openrouter() -> bool:
    base_url = getEnv("AI_ENRICH_OPENROUTER_BASE_URL", OPENROUTER_DEFAULT_BASE_URL)
    api_key = getEnv("AI_ENRICH_OPENROUTER_API_KEY") or getEnv("OPENROUTER_API_KEY", "")
    timeout = int(getEnv("HEALTHCHECK_TIMEOUT", "5"))
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def check_backend() -> bool:
    backend = getEnv("HEALTHCHECK_BACKEND", getEnv("AI_ENRICH_LLM_BACKEND", getEnv("AI_ENRICHSKILL_BACKEND", "ollama")))
    if backend == "openrouter":
        return check_openrouter()
    return check_ollama()


if __name__ == "__main__":
    sys.exit(0 if check_backend() else 1)
