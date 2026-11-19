import pytest

from ..url_relevance import DOC_TIER, TUTORIAL_TIER, VIDEO_TIER, has_docs_signal, has_skill_evidence, is_generic_path, is_generic_url, looks_like_error_page, mentions_skill, skill_tokens, url_tier


@pytest.mark.parametrize("url, expected", [
    pytest.param("https://www.youtube.com/", True, id="youtube_homepage"),
    pytest.param("https://www.youtube.com", True, id="homepage_without_slash"),
    pytest.param("https://docs.aws.amazon.com/", True, id="docs_homepage"),
    pytest.param("https://duckduckgo.com/?q=Python", True, id="search_page"),
    pytest.param("https://example.com/tag/python", True, id="tag_listing"),
    pytest.param("https://example.com/login", True, id="login_page"),
    pytest.param("https://docs.python.org/3/library/asyncio.html", False, id="docs_deep_link"),
    pytest.param("https://www.youtube.com/watch?v=abc", False, id="video_deep_link"),
    pytest.param("https://www.youtube.com/results?search_query=python", True, id="scoped_video_search"),
], ids=lambda value: None)
def test_is_generic_url(url, expected):
    assert is_generic_url(url) is expected


@pytest.mark.parametrize("url, expected", [
    pytest.param("https://example.com/search?q=python", True, id="search"),
    pytest.param("https://example.com/blog/tag/python", True, id="nested_tag"),
    pytest.param("https://example.com/docs/getting-started/", False, id="docs_path"),
    pytest.param("https://example.com/tutorial/python", False, id="tutorial_path"),
], ids=lambda value: None)
def test_is_generic_path(url, expected):
    assert is_generic_path(url) is expected


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


@pytest.mark.parametrize("headline, text, skill, expected", [
    pytest.param("Acunetix Official Documentation", "Scan your apps for vulnerabilities.", "Acunetix", True, id="skill_in_headline"),
    pytest.param("Spring Batch Guide", "A short guide.", "Spring Batch", True, id="all_tokens_in_headline"),
    pytest.param("Vulnerability Scanning", "Acunetix scans. Acunetix reports. Acunetix helps.", "Acunetix", True, id="repeated_body_mentions"),
    pytest.param("Vulnerability Scanning", "Spring jobs. Batch jobs.", "Spring Batch", True, id="both_tokens_repeated"),
    pytest.param("Vulnerability Scanning", "A single Acunetix mention is not enough.", "Acunetix", False, id="single_weak_mention"),
    pytest.param("Docker Documentation", "Learn Docker volumes and containers today.", "Acunetix", False, id="unrelated_skill"),
    pytest.param("Acunetix docs", "", "Acunetix", True, id="headline_only"),
], ids=lambda value: None)
def test_has_skill_evidence(headline, text, skill, expected):
    assert has_skill_evidence(headline, text, skill) is expected


@pytest.mark.parametrize("url, headline, expected", [
    pytest.param("https://www.acunetix.com/support/docs/introduction/", "Introduction", True, id="docs_in_path"),
    pytest.param("https://docs.python.org/3/", "Python", True, id="docs_host"),
    pytest.param("https://example.com/guide", "Acunetix reference manual", True, id="docs_in_headline"),
    pytest.param("https://example.com/blog/post", "News", False, id="no_docs_signal"),
], ids=lambda value: None)
def test_has_docs_signal(url, headline, expected):
    assert has_docs_signal(url, headline) is expected


@pytest.mark.parametrize("text, expected", [
    pytest.param("Acunetix documentation page not found", True, id="soft_404"),
    pytest.param("Just a moment... Checking your browser", True, id="bot_challenge"),
    pytest.param("Access denied — sign in to continue", True, id="login_wall"),
    pytest.param("Enable JavaScript and cookies to continue", True, id="js_interstitial"),
    pytest.param("Acunetix documentation for beginners", False, id="real_docs_page"),
], ids=lambda value: None)
def test_looks_like_error_page(text, expected):
    assert looks_like_error_page(text) is expected


@pytest.mark.parametrize("url, expected", [
    pytest.param("https://docs.python.org/3/", DOC_TIER, id="docs"),
    pytest.param("https://www.coursera.org/learn/python", TUTORIAL_TIER, id="tutorial"),
    pytest.param("https://www.youtube.com/watch?v=abc", VIDEO_TIER, id="video"),
    pytest.param("https://youtu.be/abc", VIDEO_TIER, id="short_video"),
], ids=lambda value: None)
def test_url_tier(url, expected):
    assert url_tier(url) == expected
