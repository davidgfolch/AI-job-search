import pytest
from unittest.mock import MagicMock, patch

from ..link_validator import SEARCH_FALLBACK, build_learning_path, http_probe, validate_learning_paths

DOMAINS = ("docs.python.org", "python.org", "realpython.com")


def probe_from(ok_urls):
    def probe(url, _timeout):
        return url in ok_urls
    return probe


@pytest.mark.parametrize("urls, ok_urls, max_links, expected", [
    pytest.param(
        ["https://docs.python.org/3/", "https://realpython.com/"],
        {"https://docs.python.org/3/", "https://realpython.com/"},
        3,
        ["https://docs.python.org/3/", "https://realpython.com/"],
        id="all_reachable"),
    pytest.param(
        ["https://docs.python.org/3/library/asyncio.html"],
        {"https://docs.python.org/"},
        3,
        ["https://docs.python.org/"],
        id="dead_deep_link_degrades_to_root"),
    pytest.param(
        ["https://docs.python.org/1/", "https://realpython.com/"],
        set(),
        3,
        [SEARCH_FALLBACK.format(query="Python")],
        id="all_dead_degrades_to_search"),
    pytest.param(
        ["https://example.com/tutorial"],
        {"https://example.com/tutorial"},
        3,
        [SEARCH_FALLBACK.format(query="Python")],
        id="disallowed_domain_is_dropped"),
    pytest.param(
        ["https://docs.python.org/3/", "https://realpython.com/", "https://python.org/"],
        {"https://docs.python.org/3/", "https://realpython.com/", "https://python.org/"},
        2,
        ["https://docs.python.org/3/", "https://realpython.com/"],
        id="caps_at_max_links"),
    pytest.param(
        ["https://docs.python.org/3/#intro", "https://docs.python.org/3/"],
        {"https://docs.python.org/3/"},
        3,
        ["https://docs.python.org/3/"],
        id="dedupes_same_page"),
    pytest.param(
        ["http://docs.python.org/3/"],
        {"http://docs.python.org/3/"},
        3,
        ["http://docs.python.org/3/"],
        id="accepts_http"),
], ids=lambda value: None)
def test_build_learning_path(urls, ok_urls, max_links, expected):
    result = build_learning_path("Python", urls, probe=probe_from(ok_urls), domains=DOMAINS, max_links=max_links)
    assert result == expected


def test_build_learning_path_probe_exception_is_a_dead_link():
    def probe(url, _timeout):
        if url == "https://docs.python.org/3/":
            raise RuntimeError("boom")
        return True

    result = build_learning_path("Python", ["https://docs.python.org/3/"], probe=probe, domains=DOMAINS)
    assert result == ["https://docs.python.org/"]


def test_build_learning_path_search_fallback_encodes_skill_name():
    result = build_learning_path("C++", ["https://example.com"], probe=lambda *_args: True, domains=DOMAINS)
    assert result == [SEARCH_FALLBACK.format(query="C%2B%2B")]


def test_build_learning_path_empty_skill_name_uses_generic_query():
    result = build_learning_path("", [], probe=lambda *_args: True, domains=DOMAINS)
    assert result == [SEARCH_FALLBACK.format(query="technology")]


@pytest.mark.parametrize("head_status, get_status, expected", [
    pytest.param(200, None, True, id="head_ok"),
    pytest.param(204, None, True, id="head_no_content"),
    pytest.param(404, 200, False, id="head_not_found"),
    pytest.param(403, 200, True, id="head_forbidden_falls_back_to_get"),
    pytest.param(405, 200, True, id="head_method_not_allowed_falls_back_to_get"),
    pytest.param(501, 500, False, id="get_also_fails"),
], ids=lambda value: None)
@patch("aiEnrichSkill.services.link_validator.requests")
def test_http_probe(mock_requests, head_status, get_status, expected):
    head = MagicMock(status_code=head_status)
    mock_requests.head.return_value = head
    if get_status is not None:
        mock_requests.get.return_value = MagicMock(status_code=get_status)
    assert http_probe("https://docs.python.org/", 5) is expected


@patch("aiEnrichSkill.services.link_validator.requests")
def test_http_probe_request_exception_is_dead(mock_requests):
    import requests
    mock_requests.RequestException = requests.RequestException
    mock_requests.head.side_effect = requests.RequestException("timeout")
    assert http_probe("https://docs.python.org/", 5) is False


def test_validate_learning_paths_empty_urls_skips_network():
    with patch("aiEnrichSkill.services.link_validator.http_probe") as mock_probe:
        assert validate_learning_paths("Python", []) == []
    mock_probe.assert_not_called()


@patch("aiEnrichSkill.services.link_validator.get_learning_paths_enabled", return_value=True)
@patch("aiEnrichSkill.services.link_validator.http_probe", return_value=True)
@patch("aiEnrichSkill.services.link_validator.get_learning_path_timeout", return_value=7)
@patch("aiEnrichSkill.services.link_validator.get_learning_path_max", return_value=2)
@patch("aiEnrichSkill.services.link_validator.get_learning_domains", return_value=["docs.python.org"])
def test_validate_learning_paths_uses_config(_domains, _max, _timeout, mock_probe, _enabled):
    urls = ["https://docs.python.org/3/", "https://example.com/"]
    result = validate_learning_paths("Python", urls)
    assert result == ["https://docs.python.org/3/"]
    assert mock_probe.call_args[0][1] == 7


@patch("aiEnrichSkill.services.link_validator.get_learning_paths_enabled", return_value=False)
def test_validate_learning_paths_respects_kill_switch(_enabled):
    assert validate_learning_paths("Python", ["https://docs.python.org/3/"]) == []
