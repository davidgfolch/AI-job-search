"""Deterministic grounding of the extracted hybrid detail against the offer text.

The model invents arrangement details the offer never states: a fully remote offer
comes back as "2 days per week in the office and 5 days per week remote", and a bare
"Hybrid" offer gets a schedule nobody wrote. Storing that text renders an invention
as if the offer had said it, so every claim is checked against the offer and the
whole value is discarded when it cannot be anchored:

* an arrangement side the value names (office or remote) must be mentioned by the offer;
* every number in the value must appear in the offer;
* office days plus remote days cannot exceed a working week.

Translation is allowed through synonym groups (`oficina`/`office`, `teletrabajo`/`remote`),
but a detail that cannot be traced back to the offer is dropped rather than stored.
"""
import re

from .technology_grounding import _normalize

OFFICE_WORDS = ("office", "oficina", "on site", "onsite", "on-site", "presencial", "escritorio", "in person", "in-person", "lugar de trabajo")
REMOTE_WORDS = ("remote", "remoto", "teletrabajo", "work from home", "wfh", "home", "casa", "desde casa")
_ARRANGEMENT_SIDES = (("office", OFFICE_WORDS), ("remote", REMOTE_WORDS))
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_DAY_COUNT = re.compile(r"(\d+)\s*(?:days?|dias?|días?)")
_WINDOW = 40


def _word_pattern(word: str) -> re.Pattern:
    return re.compile(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])")


def _mentions(text: str, words) -> bool:
    return any(_word_pattern(word).search(text) for word in words)


def _first_side(segment: str) -> str | None:
    """Side named first in the text that follows a day count ("3 days remote")."""
    nearest = None
    for side, words in _ARRANGEMENT_SIDES:
        for word in words:
            found = _word_pattern(word).search(segment)
            if found and (nearest is None or found.start() < nearest[0]):
                nearest = (found.start(), side)
    return nearest[1] if nearest else None


def _last_side(segment: str) -> str | None:
    """Side named last before a day count when it reads backwards ("office 3 days")."""
    nearest = None
    for side, words in _ARRANGEMENT_SIDES:
        for word in words:
            for found in _word_pattern(word).finditer(segment):
                if nearest is None or found.start() > nearest[0]:
                    nearest = (found.start(), side)
    return nearest[1] if nearest else None


def _day_counts(value: str) -> dict[str, int]:
    matches = list(_DAY_COUNT.finditer(value))
    counts: dict[str, int] = {}
    for index, match in enumerate(matches):
        segment = value[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(value)]
        side = _first_side(segment) or _last_side(value[max(0, match.start() - _WINDOW):match.start()])
        if side:
            counts[side] = counts.get(side, 0) + int(match.group(1))
    return counts


def _numbers_not_in_offer(value: str, offer: str) -> list[str]:
    return sorted({number for number in _NUMBER.findall(value) if not re.search(rf"(?<![0-9.,]){re.escape(number)}(?![0-9])", offer)})


def _ungrounded_reasons(value: str, offer: str) -> list[str]:
    reasons = [f"{side}_not_in_offer" for side, words in _ARRANGEMENT_SIDES if _mentions(value, words) and not _mentions(offer, words)]
    if _numbers_not_in_offer(value, offer):
        reasons.append("numbers_not_in_offer")
    days = _day_counts(value)
    if days.get("office") and days.get("remote") and days["office"] + days["remote"] > 5:
        reasons.append("more_days_than_week")
    return reasons


def filter_ungrounded_hybrid_info(result: dict, markdown: str, log=None) -> dict:
    """Drop a hybrid detail absent from `markdown`; mutates and returns `result`."""
    value = result.get("hybrid_info")
    if not isinstance(value, str) or not value.strip():
        result["hybrid_info"] = None
        return result
    reasons = _ungrounded_reasons(_normalize(value), _normalize(markdown))
    if reasons:
        if log is not None:
            log.warning("ai.invalid_hybrid_info", reason=",".join(reasons), hybrid_info=value)
        result["hybrid_info"] = None
    return result
