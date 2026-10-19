import urllib.request

from commonlib.network.ollama_discovery import DEFAULT_OLLAMA_PORT

try:
    import requests
except Exception:
    requests = None


def verify_ollama(host, port=None, timeout=3):
    """Verify host serves the Ollama HTTP API (GET /api/tags)."""
    port = port or DEFAULT_OLLAMA_PORT
    url = f"http://{host}:{port}/api/tags"
    if requests is not None:
        try:
            resp = requests.get(url, timeout=timeout)
            try:
                resp.raise_for_status()
            except Exception:
                return False
            status = getattr(resp, "status_code", 200)
            return 200 <= int(status) < 300
        except Exception:
            pass
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            return int(status) == 200
    except Exception:
        return False
