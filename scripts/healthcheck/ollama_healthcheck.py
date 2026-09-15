#!/usr/bin/env python
"""Healthcheck script for AI-backend-dependent services.
Returns exit code 0 if the configured backend (Ollama or OpenRouter) is reachable, 1 otherwise.
Used by Docker HEALTHCHECK to mark container as unhealthy when the backend is down."""
import os
import sys
import requests

from commonlib.ollama_config import OLLAMA_DOCKER_BASE_URL

OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def check_ollama() -> bool:
    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_DOCKER_BASE_URL)
    timeout = int(os.getenv("HEALTHCHECK_TIMEOUT", "5"))
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def check_openrouter() -> bool:
    base_url = os.getenv("AI_ENRICH_OPENROUTER_BASE_URL", OPENROUTER_DEFAULT_BASE_URL)
    api_key = os.getenv("AI_ENRICH_OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
    timeout = int(os.getenv("HEALTHCHECK_TIMEOUT", "5"))
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def check_backend() -> bool:
    backend = os.getenv("HEALTHCHECK_BACKEND", os.getenv("AI_ENRICH_BACKEND", os.getenv("AI_ENRICHSKILL_BACKEND", "ollama")))
    if backend == "openrouter":
        return check_openrouter()
    return check_ollama()


if __name__ == "__main__":
    sys.exit(0 if check_backend() else 1)
