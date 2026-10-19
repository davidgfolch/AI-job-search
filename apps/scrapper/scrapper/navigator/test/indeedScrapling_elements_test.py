import pytest
from scrapper.navigator.indeedScrapling_elements import (
    _extract_text, _extract_location, _modality_badge, _extract_total_from_title,
    CSS_SEL_JOB_TITLE, CSS_SEL_COMPANY, CSS_SEL_LOCATION, CSS_SEL_JOB_SALARY,
    CSS_SEL_JOB_DESCRIPTION, CSS_SEL_JOB_EASY_APPLY, DELISTED_TITLE,
)


class MockSelector:
    def __init__(self, text="", html=""):
        self._text = text
        self._html = html

    def get(self, default=None):
        return self._text or default

    def css(self, selector):
        return MockSelector(self._text)

    def get_all_text(self):
        return self._text

    def __bool__(self):
        return bool(self._text)


def test_extract_text_first_selector():
    page = MockSelector(text="Software Engineer")
    result = _extract_text(page, [CSS_SEL_JOB_TITLE[0]])
    assert result == "Software Engineer"


def test_extract_text_falls_back_to_second_selector():
    page = MockSelector(text="")
    page2 = MockSelector(text="Fallback Title")
    page.css = lambda sel: page2 if "fallback" in sel else MockSelector("")
    result = _extract_text(page, ["nonexistent", "fallback"])
    assert result == "Fallback Title"


def test_extract_text_empty_when_no_match():
    page = MockSelector(text="")
    result = _extract_text(page, [CSS_SEL_JOB_TITLE[0]])
    assert result == ""


def test_extract_location():
    page = MockSelector()
    page.css = lambda sel: MockSelector(text="Madrid, Spain") if "companyLocation" in sel else MockSelector("")
    result = _extract_location(page)
    assert result == "Madrid, Spain"


def test_modality_badge_remote():
    page = MockSelector()
    page.css = lambda sel: [MockSelector(text="Teletrabajo")]
    result = _modality_badge(page)
    assert result == "Teletrabajo"


def test_modality_badge_no_match():
    page = MockSelector()
    page.css = lambda sel: [MockSelector(text="Something else")]
    result = _modality_badge(page)
    assert result == ""


def test_extract_total_from_title():
    page = MockSelector()
    page.css = lambda sel: MockSelector(text="534 empleos de Ingeniero | Indeed") if sel == "title::text" else MockSelector("")
    result = _extract_total_from_title(page)
    assert result == 534


def test_extract_total_from_title_no_match():
    page = MockSelector()
    page.css = lambda sel: MockSelector(text="No results")
    result = _extract_total_from_title(page)
    assert result == 0


def test_constants_defined():
    assert DELISTED_TITLE == "No podemos encontrar esta página"
    assert len(CSS_SEL_JOB_TITLE) > 0
    assert len(CSS_SEL_COMPANY) > 0
    assert len(CSS_SEL_LOCATION) > 0
    assert len(CSS_SEL_JOB_SALARY) > 0
    assert len(CSS_SEL_JOB_DESCRIPTION) > 0
    assert len(CSS_SEL_JOB_EASY_APPLY) > 0
