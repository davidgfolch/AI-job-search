"""Deterministic modality extraction.

A job offer can allow more than one modality at once (``"remote or hybrid
collaboration"``), so the extractor returns every modality the text states
instead of collapsing them into a single value. It intentionally avoids LLMs
and zero-shot models: the result is reproducible and suitable for filter rules.
"""

from __future__ import annotations

import re

REMOTE = "REMOTE"
HYBRID = "HYBRID"
ON_SITE = "ON_SITE"

# Canonical order used for storage and for API responses.
MODALITIES = (REMOTE, HYBRID, ON_SITE)

_REMOTE_TERMS = ("teletrabajo", "remoto", "remote", "work from home", "desde casa", "work remotely")
_HYBRID_TERMS = ("híbrido", "hibrido", "hybrid", "semi-presencial", "semipresencial", "semi presencial", "mixto")
_ONSITE_TERMS = ("presencial", "on-site", "onsite", "in office", "en oficina", "on site")
# Hybrid spellings that contain the on-site cue "presencial".
_SEMI_ONSITE_TERMS = ("semi-presencial", "semipresencial", "semi presencial")

_EXPLICIT_PATTERN = re.compile(
    r"modalidad(?:\s+de\s+(?:trabajo|empleo))?\s*[:\-]\s*([a-záéíóúüñ0-9 %()/.,-]+)",
    re.IGNORECASE,
)


def _cues(text: str) -> tuple[bool, bool, bool]:
    lowered = (text or "").casefold()
    hybrid = any(term.casefold() in lowered for term in _HYBRID_TERMS)
    remote = any(term.casefold() in lowered for term in _REMOTE_TERMS)
    # "semipresencial" means hybrid, not on-site: drop those spellings before
    # looking for the on-site cue they contain.
    onsite_text = lowered
    for term in _SEMI_ONSITE_TERMS:
        onsite_text = onsite_text.replace(term, " ")
    onsite = any(term.casefold() in onsite_text for term in _ONSITE_TERMS)
    return remote, hybrid, onsite


def _flags_to_modalities(remote: bool, hybrid: bool, onsite: bool) -> list[str]:
    found = {name for name, flag in zip(MODALITIES, (remote, hybrid, onsite), strict=True) if flag}
    return [name for name in MODALITIES if name in found]


def extract_modalities(title: str = "", location: str = "", markdown: str = "") -> list[str]:
    """Return every modality the offer states, in canonical order.

    An empty list means the modality could not be determined; callers should
    store ``NULL`` and let filter rules treat it as unknown.
    """
    text = "\n".join(str(part or "") for part in (title, location, markdown))
    if match := _EXPLICIT_PATTERN.search(text):
        explicit = _flags_to_modalities(*_cues(match.group(1)))
        if explicit:
            return explicit
    return _flags_to_modalities(*_cues(text))


def normalize_modalities(value: object) -> list[str]:
    """Normalize a DB string, an API list, or a single value into MODALITIES order.

    Accepts ``"REMOTE,HYBRID"``, ``["hybrid", "REMOTE"]`` or ``None``; unknown
    values are dropped and duplicates removed.
    """
    if value is None:
        return []
    if isinstance(value, str):
        parts: list[object] = [value]
    elif isinstance(value, (list, tuple, set, frozenset)):
        parts = list(value)
    else:
        parts = [value]
    found: set[str] = set()
    for part in parts:
        for token in str(part).split(","):
            token = token.strip().upper()
            if token in MODALITIES:
                found.add(token)
    return [name for name in MODALITIES if name in found]


def modalities_to_db(value: object) -> str | None:
    """Format modalities as the comma-separated MySQL SET value, ``None`` when empty."""
    return ",".join(normalize_modalities(value)) or None
