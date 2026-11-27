import json
import re
from typing import List, NamedTuple, Tuple

URL_RE = re.compile(r'https?://[^\s<>"\']+')
_SECTION_PREFIX = r'[ \t>*#-]*(?:\d+[.)][ \t]*)?[ \t>*#-]*'
_SECTION_END = r'(?=^[ \t>*#-]*(?:Category|Summary|Deep Technical Details)[ \t>*#]*:|\Z)'
LEARNING_PATH_SECTION_RE = re.compile(
    _SECTION_PREFIX + r'Learning Path[ \t>*#]*:?[ \t]*\n?(?P<body>.*?)' + _SECTION_END,
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
_TRAILING_CHARS = '.,;:!?)]}>"\'`*'

SOURCE_LLM = "llm"
SOURCE_DUCKDUCKGO = "duckduckgo"
SOURCE_MANUAL = "manual"
SOURCE_UNKNOWN = "unknown"
LEARNING_PATH_SOURCES = (SOURCE_LLM, SOURCE_DUCKDUCKGO, SOURCE_MANUAL, SOURCE_UNKNOWN)


class LearningPathLink(NamedTuple):
    url: str
    source: str = SOURCE_UNKNOWN


def _clean_url(url: str) -> str:
    return url.strip().rstrip(_TRAILING_CHARS)


def dedupe_urls(urls: List[str]) -> List[str]:
    seen = set()
    result = []
    for raw in urls:
        url = _clean_url(raw)
        if not url:
            continue
        key = url.rstrip('/').lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(url)
    return result


def split_learning_path_section(text: str) -> Tuple[str, str]:
    """Return the text without its Learning Path section plus that section body ('' when absent)."""
    match = LEARNING_PATH_SECTION_RE.search(text)
    if not match:
        return text, ""
    body = match.group('body')
    cleaned = (text[:match.start()] + text[match.end():]).strip()
    return cleaned, body


def parse_learning_path_urls(text: str) -> List[str]:
    """URLs from the Learning Path section, falling back to any URL in the text when there is no header."""
    _, body = split_learning_path_section(text)
    source = body if body else text
    return dedupe_urls(URL_RE.findall(source))


def parse_skill_llm_output(result: str) -> tuple[str, str, List[str]]:
    """Parse LLM output into (description, category, learning_path), stripping the learning-path section first."""
    result, learning_path_body = split_learning_path_section(result)
    learning_path = dedupe_urls(URL_RE.findall(learning_path_body)) if learning_path_body else []
    category = "Other"
    description = result
    match = re.search(r'(?:^|\n)[#*]*\s*Category\s*[#*]*\s*:\s*(.+)', result, re.IGNORECASE)
    if match:
        category = match.group(1).strip().split('\n')[0].strip().replace('*', '').replace('`', '').strip()
        description = result[match.end():].strip() if match.start() == 0 else result[:match.start()].strip()
    return description, category, learning_path


def _known_source(value) -> str:
    source = str(value or SOURCE_UNKNOWN).strip().lower()
    return source if source in LEARNING_PATH_SOURCES else SOURCE_UNKNOWN


def _to_link(item) -> LearningPathLink | None:
    """Accept new objects, legacy plain strings and anything with url/source attributes."""
    if isinstance(item, str):
        url = item.strip()
        return LearningPathLink(url, SOURCE_UNKNOWN) if url else None
    if isinstance(item, dict):
        url = str(item.get("url") or "").strip()
        return LearningPathLink(url, _known_source(item.get("source"))) if url else None
    url = str(getattr(item, "url", "") or "").strip()
    if not url:
        return None
    return LearningPathLink(url, _known_source(getattr(item, "source", SOURCE_UNKNOWN)))


def deserialize_learning_path(raw) -> List[LearningPathLink]:
    """Read both the new [{url, source}] shape and legacy string arrays without losing either."""
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return []
    if not isinstance(raw, list):
        return []
    return [link for item in raw if (link := _to_link(item)) is not None]


def learning_path_as_dicts(raw) -> List[dict]:
    """Plain dicts for API models, which do not validate namedtuples from arbitrary objects."""
    return [link._asdict() for link in deserialize_learning_path(raw)]


def serialize_learning_path(links) -> str | None:
    """Persist url + source for every link; None means 'no links' for the SQL column."""
    items = [link._asdict() for link in deserialize_learning_path(links)]
    return json.dumps(items) if items else None
