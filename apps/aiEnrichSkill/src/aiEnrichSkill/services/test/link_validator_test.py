from unittest.mock import patch

import pytest
from commonlib.skill_learning_path import SOURCE_DUCKDUCKGO, SOURCE_LLM, LearningPathLink

from ...domain.url_relevance import DOC_TIER, TUTORIAL_TIER, VIDEO_TIER
from ..link_validator import build_learning_path, validate_learning_paths

DOMAINS = ("docs.python.org", "python.org", "realpython.com", "youtube.com", "coursera.org")
PYTHON_DOCS = "https://docs.python.org/3/library/asyncio.html"
PYTHON_VIDEO = "https://www.youtube.com/watch?v=python-basics"
ACUNETIX_DOCS = "https://www.acunetix.com/support/docs/introduction/"


def links(urls, source=SOURCE_LLM):
    return [LearningPathLink(url, source) for url in urls]


def verify_from(ok_urls):
    def verify(url, _skill, _timeout):
        return url in ok_urls
    return verify


def no_search(*_args):
    return []


def search_from(result, calls=None):
    def search(skill, tiers, timeout, limit):
        if calls is not None:
            calls.append((skill, list(tiers), timeout, limit))
        return result
    return search


@pytest.mark.parametrize("urls, ok_urls, max_links, expected", [
    pytest.param([PYTHON_DOCS, "https://realpython.com/python-asyncio/"], {PYTHON_DOCS, "https://realpython.com/python-asyncio/"}, 3, [PYTHON_DOCS, "https://realpython.com/python-asyncio/"], id="all_reachable"),
    pytest.param([PYTHON_DOCS], set(), 3, [], id="dead_link_dropped"),
    pytest.param(["https://example.com/tutorial"], {"https://example.com/tutorial"}, 3, ["https://example.com/tutorial"], id="off_allowlist_accepted_when_verified"),
    pytest.param([PYTHON_DOCS, "https://realpython.com/python-asyncio/", "https://python.org/about/"], {PYTHON_DOCS, "https://realpython.com/python-asyncio/", "https://python.org/about/"}, 2, [PYTHON_DOCS, "https://realpython.com/python-asyncio/"], id="caps_at_max_links"),
    pytest.param([PYTHON_DOCS + "#intro", PYTHON_DOCS], {PYTHON_DOCS}, 3, [PYTHON_DOCS], id="dedupes_same_page"),
    pytest.param(["http://docs.python.org/3/library/asyncio.html"], {"http://docs.python.org/3/library/asyncio.html"}, 3, ["http://docs.python.org/3/library/asyncio.html"], id="accepts_http"),
    pytest.param(["https://www.youtube.com/"], {"https://www.youtube.com/"}, 3, [], id="homepage_dropped"),
    pytest.param(["https://www.youtube.com/playlist?list=PL123"], {"https://www.youtube.com/playlist?list=PL123"}, 3, [], id="playlist_dropped"),
    pytest.param(["https://duckduckgo.com/?q=Python+documentation"], {"https://duckduckgo.com/?q=Python+documentation"}, 3, [], id="search_url_dropped"),
    pytest.param([PYTHON_VIDEO, "https://www.youtube.com/watch?v=abc123"], {PYTHON_VIDEO}, 3, [PYTHON_VIDEO], id="unrelated_video_dropped"),
    pytest.param([PYTHON_VIDEO, PYTHON_DOCS], {PYTHON_VIDEO, PYTHON_DOCS}, 3, [PYTHON_DOCS, PYTHON_VIDEO], id="docs_first_video_secondary"),
    pytest.param([PYTHON_VIDEO, "https://www.coursera.org/learn/python", PYTHON_DOCS], {PYTHON_VIDEO, "https://www.coursera.org/learn/python", PYTHON_DOCS}, 3, [PYTHON_DOCS, "https://www.coursera.org/learn/python", PYTHON_VIDEO], id="orders_docs_tutorial_video"),
], ids=lambda value: None)
def test_build_learning_path_tags_llm_urls(urls, ok_urls, max_links, expected):
    result = build_learning_path("Python", urls, verify=verify_from(ok_urls), search=no_search, domains=DOMAINS, max_links=max_links)
    assert result == links(expected)


def test_preferred_domains_rank_ahead_of_off_allowlist_pages():
    off_list = "https://acme-widgets.dev/docs/guide"
    result = build_learning_path("Python", [off_list, PYTHON_DOCS], verify=lambda *_args: True, search=no_search, domains=DOMAINS)
    assert result == links([PYTHON_DOCS, off_list])


def test_search_fills_missing_tiers_with_verified_real_page():
    calls = []
    result = build_learning_path("Acunetix", [], verify=verify_from({ACUNETIX_DOCS}), search=search_from([ACUNETIX_DOCS], calls), domains=DOMAINS, timeout=6, search_results=4)
    assert result == links([ACUNETIX_DOCS], SOURCE_DUCKDUCKGO)
    assert calls == [("Acunetix", [DOC_TIER, TUTORIAL_TIER], 6, 4)]


def test_search_result_off_allowlist_is_accepted_when_verified():
    result = build_learning_path("Acunetix", [], verify=lambda *_args: True, search=search_from([ACUNETIX_DOCS]), domains=("docs.python.org",))
    assert result == links([ACUNETIX_DOCS], SOURCE_DUCKDUCKGO)


def test_llm_source_wins_when_search_returns_the_same_url():
    result = build_learning_path("Python", [PYTHON_DOCS], verify=lambda *_args: True, search=search_from([PYTHON_DOCS]), domains=DOMAINS)
    assert result == links([PYTHON_DOCS], SOURCE_LLM)


def test_search_result_is_dropped_when_not_verified():
    result = build_learning_path("Acunetix", [], verify=lambda *_args: False, search=search_from([ACUNETIX_DOCS]), domains=DOMAINS)
    assert result == []


def test_search_not_called_when_links_already_filled():
    calls = []
    result = build_learning_path("Python", [PYTHON_DOCS, "https://realpython.com/python-asyncio/"], verify=lambda *_args: True, search=search_from([ACUNETIX_DOCS], calls), domains=DOMAINS, max_links=2)
    assert result == links([PYTHON_DOCS, "https://realpython.com/python-asyncio/"])
    assert calls == []


def test_video_tier_searched_only_when_model_requested_a_video():
    calls = []
    build_learning_path("Python", [PYTHON_DOCS], verify=verify_from({PYTHON_DOCS}), search=search_from([], calls), domains=DOMAINS, max_links=3)
    assert TUTORIAL_TIER in calls[0][1]
    assert VIDEO_TIER not in calls[0][1]
    calls.clear()
    build_learning_path("Python", [PYTHON_VIDEO], verify=verify_from(set()), search=search_from([], calls), domains=DOMAINS, max_links=3)
    assert VIDEO_TIER in calls[0][1]


def test_verify_exception_is_a_dead_link():
    def verify(url, _skill, _timeout):
        if url == PYTHON_DOCS:
            raise RuntimeError("boom")
        return True

    result = build_learning_path("Python", [PYTHON_DOCS, "https://realpython.com/python-asyncio/"], verify=verify, search=no_search, domains=DOMAINS)
    assert result == links(["https://realpython.com/python-asyncio/"])


@patch("aiEnrichSkill.services.link_validator.get_learning_paths_enabled", return_value=False)
def test_validate_learning_paths_respects_kill_switch(_enabled):
    assert validate_learning_paths("Python", [PYTHON_DOCS]) == []


@patch("aiEnrichSkill.services.link_validator.get_learning_path_search_enabled", return_value=False)
@patch("aiEnrichSkill.services.link_validator.search_learning_candidates")
@patch("aiEnrichSkill.services.link_validator.verify_learning_url", return_value=True)
@patch("aiEnrichSkill.services.link_validator.get_learning_path_timeout", return_value=8)
@patch("aiEnrichSkill.services.link_validator.get_learning_path_max", return_value=2)
@patch("aiEnrichSkill.services.link_validator.get_learning_domains", return_value=("docs.python.org",))
@patch("aiEnrichSkill.services.link_validator.get_learning_paths_enabled", return_value=True)
def test_validate_learning_paths_wires_config(enabled, domains, max_links, timeout, verify, search, search_enabled):
    assert validate_learning_paths("Python", [PYTHON_DOCS]) == links([PYTHON_DOCS])
    verify.assert_called_once_with(PYTHON_DOCS, "Python", 8)
    search.assert_not_called()
    assert (enabled.return_value, domains.return_value, max_links.return_value, timeout.return_value, search_enabled.return_value) == (True, ("docs.python.org",), 2, 8, False)
