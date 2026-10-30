from commonlib.network.discovery_cache import cached_discover
from commonlib.network.ollama_discovery import (
    SPEC_LOCAL, SPEC_AUTO, discover_ollama_hosts, get_local_ip,
)
from commonlib.network.ollama_verify import verify_ollama
from commonlib.observability import get_logger

logger = get_logger("commonlib.network.ollama_resolve")


def auto_discover_host():
    """Auto-discover an Ollama host on the LAN, using and refreshing the shared cache."""
    try:
        return cached_discover("ollama", verify=verify_ollama, scan=discover_ollama_hosts, log=logger)
    except Exception as e:
        logger.warning("ollama.discovery_failed", error=str(e))
        return None


def resolve_ollama_host(spec="auto"):
    """Resolve a host spec to a reachable Ollama host IP.

    - 'local' | 'localhost' | '127.0.0.1' -> 127.0.0.1 (assumed, no probe)
    - 'auto' | 'discover' -> cached LAN discovery, first verified host excluding local
    - otherwise -> the given IP, verified as an Ollama host

    Raises ConnectionError when nothing can be resolved.
    """
    spec = (spec or "auto").strip().lower()
    if spec in SPEC_LOCAL:
        return "127.0.0.1"
    if spec in SPEC_AUTO:
        local = get_local_ip()
        host = cached_discover("ollama", verify=verify_ollama, scan=discover_ollama_hosts, log=logger, tried={local})
        if host:
            return host
        raise ConnectionError("Auto-discovery found no reachable Ollama server on the LAN")
    if verify_ollama(spec):
        return spec
    raise ConnectionError(f"Ollama host '{spec}' is not reachable or does not serve the Ollama API")
