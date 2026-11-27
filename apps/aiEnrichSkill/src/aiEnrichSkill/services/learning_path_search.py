from html.parser import HTMLParser
from typing import Callable
from urllib.parse import parse_qs, urlparse

import requests

from commonlib.observability import get_logger

from ..domain.url_relevance import DOC_TIER, TUTORIAL_TIER, VIDEO_TIER

logger = get_logger("aiEnrichSkill.learning_path_search")

DDG_HTML_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = "Mozilla/5.0 (compatible; AiJobSearch/1.0)"
QUERY_BY_TIER = {
    DOC_TIER: "{skill} official documentation",
    TUTORIAL_TIER: "{skill} hands-on tutorial",
    VIDEO_TIER: "{skill} video tutorial",
}

SearchFetchFn = Callable[[str, int], str]


class _ResultParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        values = dict(attrs)
        if "result__a" in (values.get("class") or "").split() and values.get("href"):
            self.links.append(values["href"])


def _decode_link(href: str) -> str | None:
    parsed = urlparse(href if href.startswith("http") else f"https:{href}")
    if not parsed.hostname:
        return None
    if "duckduckgo.com" in parsed.hostname:
        targets = parse_qs(parsed.query).get("uddg", [])
        return targets[0] if targets else None
    return href if parsed.scheme in ("http", "https") else None


def fetch_search_page(query: str, timeout: int) -> str:
    try:
        response = requests.get(DDG_HTML_URL, params={"q": query}, timeout=timeout, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        html = response.text
        if response.status_code != 200 or "challenge-form" in html or "anomaly.js" in html:
            logger.warning("skill.learning_path.search_challenged", query=query, status=response.status_code)
            return ""
        return html
    except requests.RequestException as exc:
        logger.warning("skill.learning_path.search_failed", query=query, error=str(exc))
        return ""


def search(query: str, timeout: int, limit: int, fetch: SearchFetchFn = fetch_search_page) -> list[str]:
    """Real URLs from one DuckDuckGo query, with its `uddg=` redirects resolved."""
    html_text = fetch(query, timeout)
    if not html_text:
        return []
    parser = _ResultParser()
    parser.feed(html_text)
    urls: list[str] = []
    for href in parser.links:
        url = _decode_link(href)
        if url and url not in urls:
            urls.append(url)
            if len(urls) >= limit:
                break
    return urls


def search_learning_candidates(skill_name: str, tiers: list[str], timeout: int, limit: int, fetch: SearchFetchFn = fetch_search_page) -> list[str]:
    """Fetch candidates with one targeted query per missing resource tier."""
    name = skill_name.strip()
    if not name or not tiers:
        return []
    candidates: list[str] = []
    for tier in tiers:
        query = QUERY_BY_TIER.get(tier)
        if not query:
            continue
        for url in search(query.format(skill=name), timeout, limit, fetch):
            if url not in candidates:
                candidates.append(url)
    return candidates
