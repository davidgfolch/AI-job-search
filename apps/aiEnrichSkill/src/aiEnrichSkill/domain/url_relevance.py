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


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _matches(host: str, domains: tuple[str, ...]) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def _compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unquote_plus(text).lower())


def is_generic_url(url: str) -> bool:
    """Homepages and search-result pages are never a learning resource for a specific skill."""
    if _matches(_host(url), SEARCH_HOSTS):
        return True
    return not urlparse(url).path.strip("/")


def skill_tokens(skill_name: str) -> list[str]:
    normalized = ALIASES.get(skill_name.strip().lower(), skill_name.strip().lower())
    return [token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 1 and token not in GENERIC_TOKENS]


def mentions_skill(url: str, skill_name: str) -> bool:
    tokens = skill_tokens(skill_name)
    if not tokens:
        return True
    compact = _compact(url)
    exact = set(re.findall(r"[a-z0-9]+", unquote_plus(url).lower()))
    return any(token in exact or (len(token) >= 3 and token in compact) for token in tokens)


def url_tier(url: str) -> str:
    host = _host(url)
    if _matches(host, VIDEO_HOSTS):
        return VIDEO_TIER
    if _matches(host, COURSE_HOSTS):
        return TUTORIAL_TIER
    return DOC_TIER
