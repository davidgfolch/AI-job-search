from unittest.mock import MagicMock, patch

import pytest
import requests

from ..page_verifier import MAX_PAGE_BYTES, MAX_SIGNAL_CHARS, Page, fetch_page, verify_learning_url, verify_page, verify_video


HEADLINE = "Acunetix Official Documentation Acunetix scanner docs"
TEXT = "Learn how to scan your web applications with Acunetix. This guide covers setting up targets, running scans and reading the vulnerability reports produced by the scanner."
DOCS_URL = "https://www.acunetix.com/support/docs/introduction/"


def page_fetch(headline=HEADLINE, text=TEXT, status=200, url=DOCS_URL):
    def _fetch(requested_url, timeout, max_bytes):
        return Page(status, headline, text, url)
    return _fetch


@patch("aiEnrichSkill.services.page_verifier.requests")
def test_fetch_page_extracts_title_heading_and_meta(mock_requests):
    response = MagicMock(status_code=200, encoding="utf-8", url=DOCS_URL)
    response.iter_content.return_value = [b"<html><head><title>Acunetix docs</title>", b"<meta name='description' content='Acunetix scanner'>", b"</head><body><h1>Acunetix</h1><p>Guide</p><script>noise</script></body></html>"]
    mock_requests.get.return_value = response
    result = fetch_page(DOCS_URL, 5)
    assert result.status == 200
    assert "Acunetix docs" in result.headline
    assert "Acunetix scanner" in result.headline
    assert "Acunetix" in result.headline
    assert "noise" not in result.text
    assert result.url == DOCS_URL
    response.close.assert_called_once()


@patch("aiEnrichSkill.services.page_verifier.requests")
def test_fetch_page_caps_body(mock_requests):
    response = MagicMock(status_code=200, encoding="utf-8", url=DOCS_URL)
    response.iter_content.return_value = [b"a" * MAX_PAGE_BYTES, b"b" * 100]
    mock_requests.get.return_value = response
    result = fetch_page(DOCS_URL, 5)
    assert len(result.text) == MAX_SIGNAL_CHARS
    assert "b" not in result.text


@patch("aiEnrichSkill.services.page_verifier.requests")
def test_fetch_page_error_status_short_circuits(mock_requests):
    mock_requests.get.return_value = MagicMock(status_code=404, url=DOCS_URL)
    assert fetch_page("https://example.com/missing", 5) == Page(404, "", "", DOCS_URL)
    mock_requests.get.return_value.iter_content.assert_not_called()


@patch("aiEnrichSkill.services.page_verifier.requests")
def test_fetch_page_request_exception_is_a_dead_link(mock_requests):
    mock_requests.RequestException = requests.RequestException
    mock_requests.get.side_effect = requests.RequestException("timeout")
    assert fetch_page(DOCS_URL, 5) == Page(0, "", "", DOCS_URL)


@pytest.mark.parametrize("url, headline, text, status, final_url, expected", [
    pytest.param(DOCS_URL, HEADLINE, TEXT, 200, DOCS_URL, True, id="relevant_page"),
    pytest.param(DOCS_URL, "Page not found", "Acunetix scanner guide", 200, DOCS_URL, False, id="soft_404"),
    pytest.param(DOCS_URL, "Docker Documentation", "Learn Docker volumes and containers in this guide.", 200, DOCS_URL, False, id="unrelated_skill"),
    pytest.param(DOCS_URL, HEADLINE, TEXT, 500, DOCS_URL, False, id="server_error"),
    pytest.param(DOCS_URL, HEADLINE, "", 200, DOCS_URL, False, id="empty_page"),
    pytest.param(DOCS_URL, HEADLINE, "Acunetix guide", 200, DOCS_URL, False, id="thin_content"),
    pytest.param(DOCS_URL, "Just a moment... Checking your browser", TEXT, 200, DOCS_URL, False, id="bot_challenge"),
    pytest.param(DOCS_URL, "Access denied", TEXT, 200, DOCS_URL, False, id="login_wall"),
    pytest.param(DOCS_URL, HEADLINE, TEXT, 200, "https://example.com/login", False, id="redirect_to_login"),
    pytest.param(DOCS_URL, HEADLINE, TEXT, 200, "https://example.com/tag/acunetix", False, id="redirect_to_listing"),
    pytest.param("https://example.com/blog/post", "News from our team", TEXT, 200, "https://example.com/blog/post", False, id="no_docs_signal"),
    pytest.param("https://www.coursera.org/learn/acunetix", HEADLINE, TEXT, 200, "https://www.coursera.org/learn/acunetix", True, id="tutorial_tier_needs_no_docs_signal"),
], ids=lambda value: None)
def test_verify_page(url, headline, text, status, final_url, expected):
    assert verify_page(url, "Acunetix", 5, page_fetch(headline, text, status, final_url)) is expected


@pytest.mark.parametrize("status, title, expected", [
    pytest.param(404, "", False, id="dead_video"),
    pytest.param(200, "Docker in 10 minutes", False, id="unrelated_video"),
    pytest.param(200, "Acunetix tutorial for beginners", True, id="matching_video"),
], ids=lambda value: None)
@patch("aiEnrichSkill.services.page_verifier.requests")
def test_verify_video(mock_requests, status, title, expected):
    response = MagicMock(status_code=status)
    response.json.return_value = {"title": title}
    mock_requests.get.return_value = response
    assert verify_video("https://www.youtube.com/watch?v=abc", "Acunetix", 5) is expected
    response.close.assert_called_once()


@patch("aiEnrichSkill.services.page_verifier.requests")
def test_verify_video_request_exception_is_dead(mock_requests):
    mock_requests.RequestException = requests.RequestException
    mock_requests.get.side_effect = requests.RequestException("timeout")
    assert verify_video("https://www.youtube.com/watch?v=abc", "Acunetix", 5) is False


@pytest.mark.parametrize("url, expected", [
    pytest.param("https://duckduckgo.com/?q=Acunetix", False, id="search_page"),
    pytest.param("https://www.youtube.com/results?search_query=acunetix", False, id="video_search"),
    pytest.param("https://www.youtube.com/", False, id="homepage"),
    pytest.param("https://www.youtube.com/playlist?list=PL123", False, id="playlist"),
    pytest.param("https://example.com/tag/acunetix", False, id="listing_page"),
    pytest.param("ftp://docs.python.org/3/", False, id="bad_scheme"),
], ids=lambda value: None)
def test_verify_learning_url_rejects_non_resources(url, expected):
    assert verify_learning_url(url, "Acunetix", 5) is expected


@patch("aiEnrichSkill.services.page_verifier.verify_video", return_value=True)
def test_verify_learning_url_checks_watch_via_oembed(mock_video):
    assert verify_learning_url("https://www.youtube.com/watch?v=abc", "Acunetix", 5) is True
    mock_video.assert_called_once()


@patch("aiEnrichSkill.services.page_verifier.verify_page", return_value=True)
def test_verify_learning_url_checks_page_content(mock_page):
    assert verify_learning_url(DOCS_URL, "Acunetix", 5) is True
    mock_page.assert_called_once()


@patch("aiEnrichSkill.services.page_verifier.verify_page", return_value=False)
def test_verify_learning_url_drops_ddg_result_when_page_fails(mock_page):
    url = "https://www.acunetix.com/support/docs/access-api-documentation/"
    assert verify_learning_url(url, "Acunetix", 5) is False
    mock_page.assert_called_once()
