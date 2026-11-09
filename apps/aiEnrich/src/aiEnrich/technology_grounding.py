"""Deterministic grounding of extracted technologies against the offer text.

The model occasionally invents technologies that the offer never mentions (for
example adding Docker/AWS to a plain Java offer). This filter drops every
technology whose normalized name does not appear literally in the offer, so a
hallucinated item never reaches the database. Translated or paraphrased names
are dropped too, which is deliberate: only names written in the offer are
trustworthy.
"""
import re
import unicodedata

TECHNOLOGY_FIELDS = ("required_technologies", "optional_technologies")
_NON_ALNUM = re.compile(r"[^a-z0-9+#./-]+")
_SINGLE_TOKEN = re.compile(r"[a-z0-9+#./-]+")


def _normalize(text) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text or "").lower())
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(_NON_ALNUM.sub(" ", plain).split())


def _terms(value) -> list[str]:
    if isinstance(value, str):
        return [term.strip() for term in value.split(",") if term.strip()]
    if isinstance(value, list):
        return [str(term).strip() for term in value if term is not None and str(term).strip()]
    return []


def _is_grounded(term: str, offer: str) -> bool:
    normalized = _normalize(term)
    if not normalized:
        return False
    if _SINGLE_TOKEN.fullmatch(normalized):
        return re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", offer) is not None
    return normalized in offer


def filter_ungrounded_technologies(result: dict, markdown: str, log=None) -> dict:
    """Drop technologies absent from `markdown`; mutates and returns `result`."""
    offer = _normalize(markdown)
    dropped = []
    for field in TECHNOLOGY_FIELDS:
        terms = _terms(result.get(field))
        if not terms:
            continue
        kept = []
        for term in terms:
            if _is_grounded(term, offer):
                kept.append(term)
            else:
                dropped.append(term)
        result[field] = kept
    if dropped and log is not None:
        log.warning("ai.ungrounded_technology", dropped=dropped)
    return result
