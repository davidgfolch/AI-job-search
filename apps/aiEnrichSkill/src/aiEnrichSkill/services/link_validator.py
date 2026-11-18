from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Sequence
from urllib.parse import quote_plus, urlparse

import requests

from commonlib.observability import get_logger

from ..config import get_learning_domains, get_learning_path_max, get_learning_path_timeout, get_learning_paths_enabled
from ..domain.url_relevance import DOC_TIER, TIER_ORDER, VIDEO_TIER, is_generic_url, mentions_skill, url_tier

logger = get_logger("aiEnrichSkill.link_validator")

ProbeFn = Callable[[str, int], bool]
SEARCH_FALLBACK = "https://duckduckgo.com/?q={query}+official+documentation"
VIDEO_SEARCH_FALLBACK = "https://www.youtube.com/results?search_query={query}"
MAX_PROBE_WORKERS = 4


def _is_allowed(url: str, domains: Sequence[str]) -> bool:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def _normalize(urls: Sequence[str], domains: Sequence[str]) -> List[str]:
    seen = set()
    result = []
    for raw in urls:
        url = (raw or "").split("#")[0].strip().rstrip('.,;:!?)]}>"\'`*')
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or not _is_allowed(url, domains):
            continue
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(url)
    return result


def _safe_probe(probe: ProbeFn, url: str, timeout: int) -> bool:
    try:
        return bool(probe(url, timeout))
    except Exception as exc:
        logger.warning("skill.learning_path.probe_failed", url=url, error=str(exc))
        return False


def _probe_all(probe: ProbeFn, urls: List[str], timeout: int) -> dict:
    if not urls:
        return {}
    with ThreadPoolExecutor(max_workers=min(MAX_PROBE_WORKERS, len(urls))) as pool:
        futures = {url: pool.submit(_safe_probe, probe, url, timeout) for url in urls}
    return {url: future.result() for url, future in futures.items()}


def _search_fallback(skill_name: str) -> str:
    return SEARCH_FALLBACK.format(query=quote_plus(skill_name.strip() or "technology"))


def _video_fallback(skill_name: str) -> str:
    return VIDEO_SEARCH_FALLBACK.format(query=quote_plus(skill_name.strip()))


def _is_relevant(skill_name: str, url: str) -> bool:
    return url_tier(url) == DOC_TIER or mentions_skill(url, skill_name)


def _dedupe(urls: List[str]) -> List[str]:
    seen = set()
    result = []
    for url in urls:
        key = url.rstrip("/").lower()
        if key not in seen:
            seen.add(key)
            result.append(url)
    return result


def build_learning_path(skill_name: str, urls: Sequence[str], *, probe: ProbeFn, domains: Sequence[str], max_links: int = 3, timeout: int = 5) -> List[str]:
    """Keep allowlisted, reachable, skill-specific deep links in docs → tutorial → video order.
    Generic homepages and unrelated links are dropped; dead links degrade to a skill-scoped
    documentation search plus a video search when one was requested, never to a domain root."""
    candidates = _normalize(urls, domains)
    relevant = [url for url in candidates if not is_generic_url(url) and _is_relevant(skill_name, url)]
    video_requested = any(url_tier(url) == VIDEO_TIER for url in candidates)
    reachable = _probe_all(probe, relevant, timeout)
    selected = [url for url in relevant if reachable.get(url)]
    if not any(url_tier(url) == DOC_TIER for url in selected):
        selected.insert(0, _search_fallback(skill_name))
    if video_requested and skill_name.strip() and not any(url_tier(url) == VIDEO_TIER for url in selected):
        selected.append(_video_fallback(skill_name))
    ordered = sorted(_dedupe(selected), key=lambda url: TIER_ORDER[url_tier(url)])
    return ordered[:max_links]


def http_probe(url: str, timeout: int) -> bool:
    """HEAD first; some docs sites only answer GET or reject HEAD with 403/405."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code < 400:
            return True
        if response.status_code not in (403, 405, 501):
            return False
        response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
        response.close()
        return response.status_code < 400
    except requests.RequestException:
        return False


def validate_learning_paths(skill_name: str, urls: Sequence[str]) -> List[str]:
    """Config-driven wrapper used by the enrichment paths; returns [] when the feature is off or the model
    produced no URL."""
    if not urls or not get_learning_paths_enabled():
        return []
    return build_learning_path(
        skill_name, urls,
        probe=http_probe,
        domains=get_learning_domains(),
        max_links=get_learning_path_max(),
        timeout=get_learning_path_timeout(),
    )
