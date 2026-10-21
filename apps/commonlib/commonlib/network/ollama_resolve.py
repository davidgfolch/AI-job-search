from commonlib.network.ollama_discovery import (
    SPEC_LOCAL, SPEC_AUTO, discover_ollama_hosts, get_local_ip,
)
from commonlib.network.ollama_verify import verify_ollama


def auto_discover_host():
    """Auto-discover an Ollama host on the LAN. Returns host IP string or None."""
    try:
        for host in discover_ollama_hosts():
            if verify_ollama(host):
                return host
        return None
    except Exception:
        return None


def resolve_ollama_host(spec="auto"):
    """Resolve a host spec to a reachable Ollama host IP.

    - 'local' | 'localhost' | '127.0.0.1' -> 127.0.0.1 (assumed, no probe)
    - 'auto' | 'discover' -> LAN scan, first verified host excluding local
    - otherwise -> the given IP, verified as an Ollama host

    Raises ConnectionError when nothing can be resolved.
    """
    spec = (spec or "auto").strip().lower()
    if spec in SPEC_LOCAL:
        return "127.0.0.1"
    if spec in SPEC_AUTO:
        local = get_local_ip()
        for host in discover_ollama_hosts():
            if local and host == local:
                continue
            if verify_ollama(host):
                return host
        raise ConnectionError("Auto-discovery found no reachable Ollama server on the LAN")
    if verify_ollama(spec):
        return spec
    raise ConnectionError(f"Ollama host '{spec}' is not reachable or does not serve the Ollama API")
