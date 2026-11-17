import re
from typing import List, Tuple

URL_RE = re.compile(r'https?://[^\s<>"\']+')
_SECTION_PREFIX = r'[ \t>*#-]*(?:\d+[.)][ \t]*)?[ \t>*#-]*'
_SECTION_END = r'(?=^[ \t>*#-]*(?:Category|Summary|Deep Technical Details)[ \t>*#]*:|\Z)'
LEARNING_PATH_SECTION_RE = re.compile(
    _SECTION_PREFIX + r'Learning Path[ \t>*#]*:?[ \t]*\n?(?P<body>.*?)' + _SECTION_END,
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
_TRAILING_CHARS = '.,;:!?)]}>"\'`*'


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
