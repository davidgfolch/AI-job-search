from unittest.mock import MagicMock, patch

import pytest
import requests

from ...domain.url_relevance import DOC_TIER, VIDEO_TIER
from ..learning_path_search import _decode_link, fetch_search_page, search, search_learning_candidates

HTML = """
<div class="result results_links">
  <h2 class="result__title"><a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.acunetix.com%2Fsupport%2Fdocs%2Fintroduction%2F&amp;rut=abc">Acunetix docs</a></h2>
  <a class="result__url" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.invicti.com%2F&amp;rut=def">docs.invicti.com</a>
</div>
<div class="result results_links">
  <h2 class="result__title"><a class="result__a" href="https://www.youtube.com/watch?v=abc123">Acunetix video</a></h2>
</div>
<div class="result results_links">
  <h2 class="result__title"><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.acunetix.com%2Fsupport%2Fdocs%2Fintroduction%2F&amp;rut=ghi">Duplicate</a></h2>
</div>
"""


@pytest.mark.parametrize("href, expected", [
    pytest.param("//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.acunetix.com%2Fsupport%2Fdocs%2Fintroduction%2F", "https://www.acunetix.com/support/docs/introduction/", id="duckduckgo_redirect"),
    pytest.param("https://www.youtube.com/watch?v=abc", "https://www.youtube.com/watch?v=abc", id="direct_link"),
    pytest.param("//example.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F", "//example.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F", id="non_ddg_redirect_untouched"),
    pytest.param("not-a-url", None, id="junk"),
], ids=lambda value: None)
def test_decode_link(href, expected):
    assert _decode_link(href) == expected


def test_search_extracts_and_dedupes_real_urls():
    result = search("Acunetix official documentation", 5, 10, lambda *_args: HTML)
    assert result == ["https://www.acunetix.com/support/docs/introduction/", "https://www.youtube.com/watch?v=abc123"]


def test_search_respects_limit():
    assert search("query", 5, 1, lambda *_args: HTML) == ["https://www.acunetix.com/support/docs/introduction/"]


def test_search_empty_response():
    assert search("query", 5, 10, lambda *_args: "") == []


def test_search_learning_candidates_queries_each_tier_and_dedupes():
    calls = []

    def fetch(query, timeout):
        calls.append((query, timeout))
        return HTML if len(calls) == 1 else "<html><a class='result__a' href='https://www.youtube.com/watch?v=abc123'>v</a></html>"

    result = search_learning_candidates("Acunetix", [DOC_TIER, VIDEO_TIER], 7, 10, fetch)
    assert calls == [("Acunetix official documentation", 7), ("Acunetix video tutorial", 7)]
    assert result[0] == "https://www.acunetix.com/support/docs/introduction/"
    assert result[-1] == "https://www.youtube.com/watch?v=abc123"
    assert len(result) == len(set(result))


@pytest.mark.parametrize("skill, tiers", [
    pytest.param("", [DOC_TIER], id="empty_skill"),
    pytest.param("Acunetix", [], id="no_tiers"),
    pytest.param("Acunetix", ["unknown"], id="unknown_tier"),
], ids=lambda value: None)
def test_search_learning_candidates_no_queries(skill, tiers):
    assert search_learning_candidates(skill, tiers, 5, 10, lambda *_args: pytest.fail("no fetch expected")) == []


@patch("aiEnrichSkill.services.learning_path_search.requests")
def test_fetch_search_page_returns_html(mock_requests):
    mock_requests.get.return_value = MagicMock(text=HTML, status_code=200)
    assert fetch_search_page("Acunetix official documentation", 5) == HTML
    args, kwargs = mock_requests.get.call_args
    assert args[0].endswith("/html/")
    assert kwargs["params"] == {"q": "Acunetix official documentation"}


@pytest.mark.parametrize("status, html", [
    pytest.param(202, HTML, id="challenge_status"),
    pytest.param(200, "<html><form id='challenge-form'></form></html>", id="challenge_markup"),
], ids=lambda value: None)
@patch("aiEnrichSkill.services.learning_path_search.requests")
def test_fetch_search_page_detects_anti_bot_challenge(mock_requests, status, html):
    mock_requests.get.return_value = MagicMock(text=html, status_code=status)
    assert fetch_search_page("Acunetix official documentation", 5) == ""


@patch("aiEnrichSkill.services.learning_path_search.requests")
def test_fetch_search_page_request_exception_is_empty(mock_requests):
    mock_requests.RequestException = requests.RequestException
    mock_requests.get.side_effect = requests.RequestException("boom")
    assert fetch_search_page("query", 5) == ""
