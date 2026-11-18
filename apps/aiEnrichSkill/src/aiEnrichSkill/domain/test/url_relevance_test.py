import pytest

from ..url_relevance import DOC_TIER, TUTORIAL_TIER, VIDEO_TIER, is_generic_url, mentions_skill, skill_tokens, url_tier


@pytest.mark.parametrize("url, expected", [
    pytest.param("https://www.youtube.com/", True, id="youtube_homepage"),
    pytest.param("https://www.youtube.com", True, id="homepage_without_slash"),
    pytest.param("https://docs.aws.amazon.com/", True, id="docs_homepage"),
    pytest.param("https://duckduckgo.com/?q=Python", True, id="search_page"),
    pytest.param("https://docs.python.org/3/library/asyncio.html", False, id="docs_deep_link"),
    pytest.param("https://www.youtube.com/watch?v=abc", False, id="video_deep_link"),
    pytest.param("https://www.youtube.com/results?search_query=python", False, id="scoped_video_search"),
], ids=lambda value: None)
def test_is_generic_url(url, expected):
    assert is_generic_url(url) is expected


@pytest.mark.parametrize("skill, expected", [
    pytest.param("C++", ["cpp"], id="cpp_alias"),
    pytest.param("Node.js", ["nodejs"], id="node_alias"),
    pytest.param("A B Testing", ["testing"], id="short_words_dropped"),
    pytest.param("Spring Batch", ["spring", "batch"], id="multi_word"),
], ids=lambda value: None)
def test_skill_tokens(skill, expected):
    assert skill_tokens(skill) == expected


@pytest.mark.parametrize("url, skill, expected", [
    pytest.param("https://www.youtube.com/watch?v=python-asyncio", "Python", True, id="matching_video"),
    pytest.param("https://www.youtube.com/watch?v=abc123", "Python", False, id="unrelated_video"),
    pytest.param("https://www.coursera.org/learn/nodejs", "Node.js", True, id="course_alias"),
    pytest.param("https://nodejs.org/api/async_hooks.html", "Node.js", True, id="dotted_alias_in_path"),
    pytest.param("https://www.youtube.com/@SpringBootPro", "Spring Batch", True, id="compound_name_in_channel"),
    pytest.param("https://www.youtube.com/watch?v=abc", "C++", False, id="no_tokens_in_video_url"),
], ids=lambda value: None)
def test_mentions_skill(url, skill, expected):
    assert mentions_skill(url, skill) is expected


@pytest.mark.parametrize("url, expected", [
    pytest.param("https://docs.python.org/3/", DOC_TIER, id="docs"),
    pytest.param("https://www.coursera.org/learn/python", TUTORIAL_TIER, id="tutorial"),
    pytest.param("https://www.youtube.com/watch?v=abc", VIDEO_TIER, id="video"),
    pytest.param("https://youtu.be/abc", VIDEO_TIER, id="short_video"),
], ids=lambda value: None)
def test_url_tier(url, expected):
    assert url_tier(url) == expected
