import re
from urllib.parse import unquote_plus, urlparse

DOC_TIER = "docs"
TUTORIAL_TIER = "tutorial"
VIDEO_TIER = "video"
TIER_ORDER = {DOC_TIER: 0, TUTORIAL_TIER: 1, VIDEO_TIER: 2}

SEARCH_HOSTS = ("duckduckgo.com", "google.com", "bing.com")
VIDEO_HOSTS = ("youtube.com", "youtu.be", "vimeo.com", "twitch.tv")
COURSE_HOSTS = ("coursera.org", "udemy.com", "edx.org", "udacity.com", "freecodecamp.org", "roadmap.sh", "classcentral.com")
GENERIC_TOKENS = {"api", "docs", "doc", "learn", "tutorial", "course", "guide", "official", "free", "full", "intro", "introduction", "the", "and", "for", "with", "of", "in"}
ALIASES = {"c++": "cpp", "c#": "csharp", "node.js": "nodejs", ".net": "dotnet", "asp.net": "aspnet"}
SOFT_404_MARKERS = ("page not found", "404 not found", "404 error", "video unavailable", "playlist does not exist", "playlist not found", "no longer available", "content not found")
ERROR_PAGE_MARKERS = SOFT_404_MARKERS + (
    "access denied", "403 forbidden", "service unavailable", "just a moment",
    "checking your browser", "enable javascript", "are you a robot", "verifying you are human",
    "attention required", "request blocked", "you have been blocked", "sign in to continue",
    "please enable cookies", "captcha", "unusual traffic",
)
DOC_PATH_MARKERS = ("docs", "documentation", "reference", "manual", "guide", "api", "tutorial", "getting-started")
DOCS_SIGNAL_MARKERS = ("documentation", "docs", "reference", "manual", "user guide", "getting started", "api reference", "tutorial")
GENERIC_PATH_SEGMENTS = {"search", "searches", "results", "suche", "buscar", "tag", "tags", "category", "categories", "sitemap", "home", "index", "login", "signin", "signup", "register", "error", "404", "500", "preview", "amp"}


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _matches(host: str, domains: tuple[str, ...]) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def _compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unquote_plus(text).lower())


def is_generic_path(url: str) -> bool:
    """Listing, auth and error paths are never a concrete learning resource."""
    segments = [segment for segment in urlparse(url).path.lower().split("/") if segment]
    return any(segment in GENERIC_PATH_SEGMENTS for segment in segments)


def is_generic_url(url: str) -> bool:
    """Homepages, search-result and listing pages are never a learning resource for a specific skill."""
    if _matches(_host(url), SEARCH_HOSTS) or is_generic_path(url):
        return True
    return not urlparse(url).path.strip("/")


def is_search_page(url: str) -> bool:
    """Search-result URLs, including YouTube's scoped search, are never a stored resource."""
    if _matches(_host(url), SEARCH_HOSTS):
        return True
    path = urlparse(url).path.rstrip("/").lower()
    return _matches(_host(url), VIDEO_HOSTS) and path in ("/results", "/search")


def is_video_watch_url(url: str) -> bool:
    """Only concrete watch URLs are acceptable: playlists and channels are often dead or invented."""
    host = _host(url)
    path = urlparse(url).path.rstrip("/").lower()
    return (_matches(host, ("youtube.com",)) and path == "/watch") or (host == "youtu.be" and bool(path.strip("/")))


def is_video_page(url: str) -> bool:
    """Any video-host URL (playlist, channel, watch) — used to drop non-watch pages early."""
    return _matches(_host(url), VIDEO_HOSTS)


def looks_like_docs(url: str) -> bool:
    """Rank documentation-style URLs ahead of generic pages within the same tier."""
    return _host(url).startswith("docs.") or any(marker in urlparse(url).path.lower() for marker in DOC_PATH_MARKERS)


def has_docs_signal(url: str, headline: str) -> bool:
    """A docs-tier candidate must look like documentation in either its path or its headings."""
    return looks_like_docs(url) or any(marker in headline.lower() for marker in DOCS_SIGNAL_MARKERS)


def skill_tokens(skill_name: str) -> list[str]:
    normalized = ALIASES.get(skill_name.strip().lower(), skill_name.strip().lower())
    return [token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 1 and token not in GENERIC_TOKENS]


def _text_mentions(text: str, tokens: list[str]) -> bool:
    if not tokens:
        return True
    compact = _compact(text)
    exact = set(re.findall(r"[a-z0-9]+", unquote_plus(text).lower()))
    return any(token in exact or (len(token) >= 3 and token in compact) for token in tokens)


def _headline_mentions(headline: str, tokens: list[str]) -> bool:
    if not tokens:
        return True
    compact = _compact(headline)
    exact = set(re.findall(r"[a-z0-9]+", headline.lower()))
    return all(token in exact or (len(token) >= 3 and token in compact) for token in tokens)


def mentions_skill(url: str, skill_name: str) -> bool:
    return _text_mentions(url, skill_tokens(skill_name))


def has_skill_evidence(headline: str, text: str, skill_name: str) -> bool:
    """Require the skill in the headline, or repeated substantive mentions in the body."""
    tokens = skill_tokens(skill_name)
    if not tokens:
        return True
    if _headline_mentions(headline, tokens):
        return True
    words = re.findall(r"[a-z0-9]+", text.lower())
    compact = _compact(text)
    counts = {token: words.count(token) + (compact.count(token) if len(token) >= 3 else 0) for token in tokens}
    return sum(1 for count in counts.values() if count >= 2) >= 2 or any(count >= 3 for count in counts.values())


def looks_like_error_page(text: str) -> bool:
    """Catch soft-404s, bot challenges, interstitials and login walls that still answer 200."""
    compact = " ".join(unquote_plus(text).lower().split())
    return any(marker in compact for marker in ERROR_PAGE_MARKERS)


def url_tier(url: str) -> str:
    host = _host(url)
    if _matches(host, VIDEO_HOSTS):
        return VIDEO_TIER
    if _matches(host, COURSE_HOSTS):
        return TUTORIAL_TIER
    return DOC_TIER
