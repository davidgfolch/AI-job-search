from html.parser import HTMLParser
from typing import Callable, NamedTuple
from urllib.parse import urlparse

import requests

from commonlib.observability import get_logger

from ..domain.url_relevance import DOC_TIER, has_docs_signal, has_skill_evidence, is_generic_path, is_search_page, is_video_page, is_video_watch_url, looks_like_error_page, url_tier

logger = get_logger("aiEnrichSkill.page_verifier")

MAX_PAGE_BYTES = 200_000
MAX_SIGNAL_CHARS = 20_000
ERROR_SCAN_CHARS = 2_000
MIN_CONTENT_CHARS = 100
USER_AGENT = "Mozilla/5.0 (compatible; AiJobSearch/1.0)"
OEMBED_URL = "https://www.youtube.com/oembed"


class Page(NamedTuple):
    status: int
    headline: str
    text: str
    url: str = ""


FetchFn = Callable[[str, int, int], Page]


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title: list[str] = []
        self.headings: list[str] = []
        self.description: list[str] = []
        self.text: list[str] = []
        self._skipped = 0
        self._in_title = False
        self._in_heading = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skipped += 1
            return
        if self._skipped:
            return
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_heading = True
        elif tag == "meta":
            values = dict(attrs)
            if (values.get("name") or "").lower() == "description" and values.get("content"):
                self.description.append(values["content"])

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skipped = max(0, self._skipped - 1)
        elif tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_heading = False

    def handle_data(self, data):
        if self._skipped:
            return
        value = data.strip()
        if not value:
            return
        self.text.append(value)
        if self._in_title:
            self.title.append(value)
        if self._in_heading:
            self.headings.append(value)

    @property
    def headline(self) -> str:
        return " ".join(self.title + self.headings + self.description)


def fetch_page(url: str, timeout: int, max_bytes: int = MAX_PAGE_BYTES) -> Page:
    """GET a bounded amount of HTML so relevance is judged from content, not just a status code."""
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True, headers={"User-Agent": USER_AGENT})
        try:
            if response.status_code >= 400:
                return Page(response.status_code, "", "", response.url)
            body = b""
            for chunk in response.iter_content(chunk_size=8192):
                body += chunk
                if len(body) >= max_bytes:
                    break
            text = body.decode(response.encoding or "utf-8", errors="replace")
            final_url = response.url
        finally:
            response.close()
    except requests.RequestException as exc:
        logger.warning("skill.learning_path.page_fetch_failed", url=url, error=str(exc))
        return Page(0, "", "", url)
    parser = _PageParser()
    parser.feed(text)
    return Page(200, parser.headline, " ".join(parser.text)[:MAX_SIGNAL_CHARS], final_url)


def verify_video(url: str, skill_name: str, timeout: int) -> bool:
    """oEmbed 404s for dead videos/playlists and returns the real title for a live video."""
    try:
        response = requests.get(OEMBED_URL, params={"url": url, "format": "json"}, timeout=timeout, headers={"User-Agent": USER_AGENT})
        try:
            if response.status_code >= 400:
                return False
            title = response.json().get("title", "")
        finally:
            response.close()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("skill.learning_path.video_probe_failed", url=url, error=str(exc))
        return False
    return has_skill_evidence(title, "", skill_name)


def verify_page(url: str, skill_name: str, timeout: int, fetch: FetchFn = fetch_page) -> bool:
    """Accept a page only when it is a real, substantive page about this exact skill."""
    page = fetch(url, timeout, MAX_PAGE_BYTES)
    if not 200 <= page.status < 300 or len(page.text) < MIN_CONTENT_CHARS:
        return False
    if looks_like_error_page(f"{page.headline} {page.text[:ERROR_SCAN_CHARS]}"):
        return False
    final_url = page.url or url
    if is_generic_path(final_url) or not urlparse(final_url).path.strip("/"):
        return False
    if not has_skill_evidence(page.headline, page.text, skill_name):
        return False
    return url_tier(url) != DOC_TIER or has_docs_signal(url, page.headline)


def verify_learning_url(url: str, skill_name: str, timeout: int, fetch: FetchFn = fetch_page) -> bool:
    """Accept only real pages/videos whose loaded content is about this exact skill."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    if is_search_page(url) or is_generic_path(url) or (not parsed.path.strip("/") and not is_video_watch_url(url)):
        return False
    if is_video_page(url):
        return is_video_watch_url(url) and verify_video(url, skill_name, timeout)
    return verify_page(url, skill_name, timeout, fetch)
