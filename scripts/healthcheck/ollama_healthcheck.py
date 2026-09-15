#!/usr/bin/env python
"""Healthcheck script for Ollama-dependent services.
Returns exit code 0 if Ollama is reachable, 1 otherwise.
Used by Docker HEALTHCHECK to mark container as unhealthy when Ollama is down."""
import os
import sys
import requests

from commonlib.ollama_config import OLLAMA_DOCKER_BASE_URL


def check_ollama() -> bool:
    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_DOCKER_BASE_URL)
    timeout = int(os.getenv("HEALTHCHECK_TIMEOUT", "5"))
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(0 if check_ollama() else 1)
