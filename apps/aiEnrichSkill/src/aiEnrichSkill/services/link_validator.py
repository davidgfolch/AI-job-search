from typing import Callable, List, Sequence
from urllib.parse import urlparse

from commonlib.observability import get_logger
from commonlib.skill_learning_path import SOURCE_DUCKDUCKGO, SOURCE_LLM, LearningPathLink

from ..config import get_learning_domains, get_learning_path_max, get_learning_path_search_enabled, get_learning_path_search_results, get_learning_path_timeout, get_learning_paths_enabled
from ..domain.url_relevance import DOC_TIER, TIER_ORDER, TUTORIAL_TIER, VIDEO_TIER, is_generic_url, is_search_page, is_video_page, is_video_watch_url, looks_like_docs, url_tier
from .learning_path_search import search_learning_candidates
from .page_verifier import verify_learning_url

logger = get_logger("aiEnrichSkill.link_validator")

VerifyFn = Callable[[str, str, int], bool]
SearchFn = Callable[[str, List[str], int, int], List[str]]


def _is_preferred(url: str, domains: Sequence[str]) -> bool:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def _sanitize(urls: Sequence[str]) -> List[str]:
    seen = set()
    result = []
    for raw in urls:
        url = (raw or "").split("#")[0].strip().rstrip('.,;:!?)]}>"\'`*')
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or is_search_page(url) or is_generic_url(url) or (is_video_page(url) and not is_video_watch_url(url)):
            continue
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(url)
    return result


def _verify_safe(verify: VerifyFn, url: str, skill_name: str, timeout: int) -> bool:
    try:
        return bool(verify(url, skill_name, timeout))
    except Exception as exc:
        logger.warning("skill.learning_path.verify_failed", url=url, error=str(exc))
        return False


def _missing_tiers(selected: List[LearningPathLink], video_requested: bool) -> List[str]:
    present = {url_tier(link.url) for link in selected}
    missing = []
    if DOC_TIER not in present:
        missing.append(DOC_TIER)
    if TUTORIAL_TIER not in present:
        missing.append(TUTORIAL_TIER)
    if video_requested and VIDEO_TIER not in present:
        missing.append(VIDEO_TIER)
    return missing


def _order(links: List[LearningPathLink], domains: Sequence[str]) -> List[LearningPathLink]:
    return sorted(links, key=lambda link: (TIER_ORDER[url_tier(link.url)], 0 if _is_preferred(link.url, domains) else 1, 0 if looks_like_docs(link.url) else 1))


def build_learning_path(skill_name: str, urls: Sequence[str], *, verify: VerifyFn, domains: Sequence[str], search: SearchFn | None = None, max_links: int = 3, timeout: int = 5, search_results: int = 10) -> List[LearningPathLink]:
    """Keep only content-verified pages, tagging each with the source that discovered it."""
    candidates = _sanitize(urls)
    selected = [LearningPathLink(url, SOURCE_LLM) for url in candidates if _verify_safe(verify, url, skill_name, timeout)]
    seen = {link.url.rstrip("/").lower() for link in selected}
    if search and len(selected) < max_links:
        video_requested = any(url_tier(url) == VIDEO_TIER for url in candidates)
        missing = _missing_tiers(selected, video_requested)
        for url in (_sanitize(search(skill_name, missing, timeout, search_results)) if missing else []):
            key = url.rstrip("/").lower()
            if key in seen or len(selected) >= max_links or not _verify_safe(verify, url, skill_name, timeout):
                continue
            selected.append(LearningPathLink(url, SOURCE_DUCKDUCKGO))
            seen.add(key)
    return _order(selected, domains)[:max_links]


def validate_learning_paths(skill_name: str, urls: Sequence[str]) -> List[LearningPathLink]:
    """Config-driven wrapper used by all enrichment paths; never stores a search-results URL."""
    if not get_learning_paths_enabled():
        return []
    return build_learning_path(
        skill_name, urls,
        verify=verify_learning_url,
        search=search_learning_candidates if get_learning_path_search_enabled() else None,
        domains=get_learning_domains(),
        max_links=get_learning_path_max(),
        timeout=get_learning_path_timeout(),
        search_results=get_learning_path_search_results(),
    )
