"""Deterministic modality extraction.

This module intentionally avoids LLMs and zero-shot models: modality is derived
from explicit text cues so the result is reproducible and suitable for filter rules.
"""

from __future__ import annotations

import re
from typing import Optional

_REMOTE_TERMS = ("teletrabajo", "remoto", "remote", "work from home", "desde casa", "work remotely")
_HYBRID_TERMS = ("híbrido", "hibrido", "hybrid", "semi-presencial", "semipresencial", "mixto")
_ONSITE_TERMS = ("presencial", "on-site", "onsite", "in office", "en oficina", "on site")

_EXPLICIT_PATTERN = re.compile(
    r"modalidad(?:\s+de\s+(?:trabajo|empleo))?\s*[:\-]\s*([a-záéíóúüñ0-9 %()/.,-]+)",
    re.IGNORECASE,
)


def _cues(text: str) -> tuple[bool, bool, bool]:
    lowered = (text or "").casefold()
    hybrid = any(term.casefold() in lowered for term in _HYBRID_TERMS)
    remote = any(term.casefold() in lowered for term in _REMOTE_TERMS)
    onsite = any(term.casefold() in lowered for term in _ONSITE_TERMS)
    return remote, hybrid, onsite


def extract_modality(title: str = "", location: str = "", markdown: str = "") -> Optional[str]:
    """Return ``REMOTE``, ``HYBRID``, ``ON_SITE`` or ``None``.

    ``None`` means the modality could not be determined; callers should store it as
    ``NULL`` and let filter rules treat it as unknown.
    """
    text = "\n".join(str(part or "") for part in (title, location, markdown))

    if match := _EXPLICIT_PATTERN.search(text):
        phrase = match.group(1)
        remote, hybrid, onsite = _cues(phrase)
        if hybrid:
            return "HYBRID"
        if remote and not onsite:
            return "REMOTE"
        if onsite and not remote:
            return "ON_SITE"
        if remote and onsite:
            return "HYBRID"

    remote, hybrid, onsite = _cues(text)
    if hybrid:
        return "HYBRID"
    if remote and onsite:
        return "HYBRID"
    if remote:
        return "REMOTE"
    if onsite:
        return "ON_SITE"
    return None