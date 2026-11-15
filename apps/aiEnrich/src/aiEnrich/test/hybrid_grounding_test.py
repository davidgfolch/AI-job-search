from unittest.mock import MagicMock

import pytest

from ..hybrid_grounding import filter_ungrounded_hybrid_info

REMOTE_ONLY_OFFER = "Remote, Full-time. Backend in Java and React with Kubernetes."
HALLUCINATED = "Hybrid work, with 2 days per week in the office and 5 days per week remote, with a flexible schedule."


def extraction(hybrid_info):
    return {"required_technologies": ["Java"], "optional_technologies": [], "salary": None, "modality": ["HYBRID"], "hybrid_info": hybrid_info}


@pytest.mark.parametrize("hybrid_info, offer", [
    ("2 days a week in the office", "Hybrid role: 2 days a week in the office, 3 days remote"),
    ("3 days remote / 2 days office", "Híbrido: 3 días en remoto y 2 días en la oficina"),
    ("2 días en la oficina", "Híbrido: 2 días en la oficina y 3 en remoto"),
    ("2 days in the office", "Híbrido: 2 días en la oficina"),
    ("teletrabajo 50%", "Modelo híbrido con teletrabajo 50%"),
    ("4 days in the office, 1 day working from home", "Hybrid. 4 days in the office, 1 day working from home"),
])
def test_grounded_hybrid_info_is_kept(hybrid_info, offer):
    assert filter_ungrounded_hybrid_info(extraction(hybrid_info), offer)["hybrid_info"] == hybrid_info


@pytest.mark.parametrize("hybrid_info, offer, reason", [
    (HALLUCINATED, REMOTE_ONLY_OFFER, "office_not_in_offer,numbers_not_in_offer,more_days_than_week"),
    ("1 day a week at the office on Wednesdays", "Hybrid; office in Madrid", "numbers_not_in_offer"),
    ("20% on-site and 80% remote", "Híbrido con 20% teletrabajo", "office_not_in_offer,numbers_not_in_offer"),
    ("2 days per week in the office and 5 days per week remote", "Hybrid. Office in Madrid, remote-friendly. 2 products, 5 teams.", "more_days_than_week"),
    ("2 days in the office", "Modelo híbrido de trabajo", "office_not_in_offer,numbers_not_in_offer"),
    ("2 days in the office", "", "office_not_in_offer,numbers_not_in_offer"),
])
def test_ungrounded_hybrid_info_is_dropped(hybrid_info, offer, reason):
    result = filter_ungrounded_hybrid_info(extraction(hybrid_info), offer)
    assert result["hybrid_info"] is None
    assert result["required_technologies"] == ["Java"]


@pytest.mark.parametrize("hybrid_info", [None, "", "   ", 42, ["two days"]])
def test_absent_or_non_string_hybrid_info_becomes_none(hybrid_info):
    assert filter_ungrounded_hybrid_info(extraction(hybrid_info), REMOTE_ONLY_OFFER)["hybrid_info"] is None


def test_logs_the_dropped_detail():
    log = MagicMock()
    filter_ungrounded_hybrid_info(extraction(HALLUCINATED), REMOTE_ONLY_OFFER, log=log)
    log.warning.assert_called_once_with("ai.invalid_hybrid_info", reason="office_not_in_offer,numbers_not_in_offer,more_days_than_week", hybrid_info=HALLUCINATED)


def test_does_not_log_when_the_detail_is_grounded():
    log = MagicMock()
    filter_ungrounded_hybrid_info(extraction("2 días en la oficina"), "Híbrido: 2 días en la oficina y 3 en remoto", log=log)
    log.warning.assert_not_called()
