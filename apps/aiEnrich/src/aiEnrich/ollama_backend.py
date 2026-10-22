import sys

from commonlib.ollama_client import query_ollama
from commonlib.ollama_probe import forget_server
from commonlib.ollama_probe import resolve_ollama_url as probe_resolve_ollama_url
from commonlib.observability import get_logger
from .aiEnrich_config import (
    get_backend, get_ollama_base_url, get_timeout_job,
    get_max_ollama_failures, get_openrouter_base_url, get_openrouter_fallback_model,
)
from .extraction_contract import COMPANY_SCHEMA, EXTRACTION_SCHEMA
from .openrouter_client import ping_openrouter, query_openrouter

logger = get_logger("aiEnrich.ollama_backend")

_resolved_ollama_url: str | None = None
_ollama_server_known = False
ollama_consecutive_failures = 0


def _get_ollama_base_url() -> str:
    return _resolved_ollama_url or get_ollama_base_url()


def _query_job(prompt: str, backend: str, model: str, response_schema: dict | None = None):
    if backend == "openrouter":
        return query_openrouter(
            prompt=prompt, model=model, base_url=get_openrouter_base_url(), timeout=get_timeout_job(), json_mode=False,
            fallback_model=get_openrouter_fallback_model(),
        )
    return query_ollama(
        prompt=prompt, model=model, primary_url=_get_ollama_base_url(), timeout=get_timeout_job(), json_mode=True,
        response_schema=response_schema or EXTRACTION_SCHEMA, return_metadata=True, log=logger,
    )


def _query_company(prompt: str, backend: str, model: str):
    """Company-only request, constrained with COMPANY_SCHEMA.

    EXTRACTION_SCHEMA must never be reused here: Ollama grammar-constrains the reply to it and its
    additionalProperties=false forbids `company`, so every response failed with "missing fields: company".
    """
    return _query_job(prompt, backend, model, COMPANY_SCHEMA)


def ping_backend() -> bool:
    global _resolved_ollama_url, _ollama_server_known
    if get_backend() == "openrouter":
        return ping_openrouter(base_url=get_openrouter_base_url())
    # Liveness checks reuse the cached server while it answers. When it stops
    # answering, drop it and resolve again: the LAN host may have gone to sleep
    # and come back on another DHCP address, so pinging the cached URL forever
    # would never find it again.
    url = probe_resolve_ollama_url(primary_url=get_ollama_base_url(), log=logger, timeout=5)
    if url is None and _resolved_ollama_url is not None:
        logger.warning("ollama.resolved_unreachable", base_url=_resolved_ollama_url)
        forget_server(_resolved_ollama_url)
    _resolved_ollama_url = url
    if _resolved_ollama_url is not None:
        _ollama_server_known = True
    return _resolved_ollama_url is not None


def _check_backend_available() -> bool:
    global ollama_consecutive_failures
    if ping_backend():
        ollama_consecutive_failures = 0
        return True
    ollama_consecutive_failures += 1
    backend = get_backend()
    max_failures = get_max_ollama_failures()
    logger.error("ai.unreachable", backend=backend, consecutive_failures=ollama_consecutive_failures, max_failures=max_failures)
    # A server this process already reached may just be asleep (e.g. a LAN host that
    # suspends), and Docker restarts cannot help there: keep waiting for it instead
    # of exiting. Only abort while no server has ever been resolved, so a genuinely
    # unreachable startup still self-heals through the container restart policy.
    known_server = backend == "ollama" and _ollama_server_known
    if ollama_consecutive_failures >= max_failures and not known_server:
        logger.critical("ai.exit_threshold_reached", consecutive_failures=ollama_consecutive_failures)
        sys.exit(1)
    return False
