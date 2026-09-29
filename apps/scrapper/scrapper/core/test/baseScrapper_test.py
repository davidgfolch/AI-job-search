import pytest
from unittest.mock import patch, MagicMock
from scrapper.core import baseScrapper
from scrapper.core.baseScrapper import (
    getAndCheckEnvVars, htmlToMarkdown, removeInvalidScapes,
    removeLinks, validate, join, printScrapperTitle, printPage, removeUrlParameter
)
from commonlib.terminalColor import stripAnsi
from scrapper.test.log_capture import captured_records

class TestGetAndCheckEnvVars:
    @pytest.mark.parametrize("side_effect, expected_email, expected_search, expected_exc", [
        (['t@e.com', 'pwd', 'py'], 't@e.com', 'py', None),
        (['t@e.com', 'pwd', None, 'gen'], 't@e.com', 'gen', None),
        ([None, 'pwd', 'search'], None, None, SystemExit),
        (['t@e.com', None, 'search'], None, None, SystemExit),
        (['t@e.com', 'pwd', None, None], None, None, SystemExit),
    ])
    @patch('scrapper.core.baseScrapper.getEnv')
    def test_get_env_vars(self, mockGetEnv, side_effect, expected_email, expected_search, expected_exc):
        mockGetEnv.side_effect = side_effect
        if expected_exc:
            with pytest.raises(expected_exc):
                getAndCheckEnvVars('LINKEDIN')
        else:
            email, pwd, search = getAndCheckEnvVars('LINKEDIN')
            if expected_email: assert email == expected_email
            assert pwd == 'pwd'
            assert search == expected_search

class TestHtmlToMarkdown:
    @pytest.mark.parametrize("html, expected", [
        ('<p>Hello World</p>', 'Hello World'),
        ('<a href="http://test.com">Link</a>', 'Link'),
        ('<p>Line1<br>Line2</p>', ['Line1', 'Line2']),
        ('<ul><li>Item1</li><li>Item2</li></ul>', ['Item1', 'Item2']),
        ('<p>Price: \\$100</p>', '$100')
    ])
    def test_html_to_markdown(self, html, expected):
        md = htmlToMarkdown(html)
        if isinstance(expected, list):
            for item in expected: assert item in md
        else:
            assert expected in md

@pytest.mark.parametrize("text, expected", [
    ('Price: \\$100', 'Price: $100'),
    ('Test\\nText\\tHere', lambda res: '\\' not in res or '\\u' in res),
    ('Unicode: \\u0041', '\\u0041')
])
def test_remove_invalid_scapes(text, expected):
    res = removeInvalidScapes(text)
    if callable(expected): assert expected(res)
    else: assert expected in res

@pytest.mark.parametrize("text, should_contain, should_not_contain", [
    ('Check [this link](http://example.com) for more', ['this link'], ['http://example.com']),
    ('[Link1](url1) and [Link2](url2)', ['Link1', 'Link2'], ['url1', 'url2']),
    ('Plain text without links', ['Plain text without links'], [])
])
def test_remove_links(text, should_contain, should_not_contain):
    res = removeLinks(text)
    for item in should_contain: assert item in res
    for item in should_not_contain: assert item not in res

@pytest.mark.parametrize("args, expected", [
    (('Title', 'http://url.com', 'Company', '# Markdown', False), True),
    (('', 'http://url.com', 'Company', '# Markdown', False), False),
    (('Title', '', 'Company', '# Markdown', False), False),
    (('Title', 'http://url.com', '', '# Markdown', False), False),
    (('Title', 'http://url.com', 'Company', '', False), False),
    (('   ', 'http://url.com', 'Company', '# Markdown', False), False),
])
def test_validate(args, expected):
    assert validate(*args) is expected



@pytest.mark.parametrize("strings, expected", [
    (('Hello', ' ', 'World'), 'Hello World'),
    (('', '', ''), ''),
    (('Single',), 'Single')
])
def test_join(strings, expected):
    assert join(*strings) == expected

@pytest.mark.parametrize("preload", [True, False], ids=["preload", "scrapping"])
@patch('scrapper.core.baseScrapper.printHR')
def test_print_scrapper_title(mock_hr, preload):
    with captured_records(baseScrapper, "scrapper.baseScrapper") as records:
        printScrapperTitle('LinkedIn', preload)
    assert [r["event"] for r in records] == ["scraper.run_starting"]
    assert records[0]["log_level"] == "info"
    assert records[0]["scrapper"] == "LinkedIn"
    assert records[0]["preload"] is preload
    assert mock_hr.call_count == 2

@patch('scrapper.core.baseScrapper.printHR')
def test_print_page(mock_hr):
    with captured_records(baseScrapper, "scrapper.baseScrapper") as records:
        printPage('LinkedIn', 1, 10, 'python developer')
    assert [r["event"] for r in records] == ["scraper.page_loaded"]
    assert records[0]["log_level"] == "info"
    assert records[0]["web_page"] == "LinkedIn"
    assert records[0]["page"] == 1
    assert records[0]["total_pages"] == 10
    assert records[0]["keywords"] == "python developer"
    assert "Starting page 1 of 10" in stripAnsi(records[0]["console"])
    mock_hr.assert_called()

def test_summarize_logs_loaded_count():
    with captured_records(baseScrapper, "scrapper.baseScrapper") as records:
        with patch('scrapper.core.baseScrapper.printHR'):
            baseScrapper.summarize('python', 120, 25)
    assert [r["event"] for r in records] == ["scraper.results_loaded"]
    assert records[0]["loaded"] == 25
    assert records[0]["total"] == 120
    assert records[0]["keywords"] == "python"

@patch('scrapper.core.baseScrapper.getEnv')
def test_get_env_vars_missing_logs_error_without_secret_values(mock_get_env):
    mock_get_env.return_value = None
    with captured_records(baseScrapper, "scrapper.baseScrapper") as records:
        with pytest.raises(SystemExit):
            getAndCheckEnvVars('LINKEDIN')
    assert [r["event"] for r in records] == ["config.env_missing"]
    assert records[0]["log_level"] == "error"
    assert records[0]["site"] == "LINKEDIN"
    assert records[0]["missing_count"] == 3
    assert records[0]["missing_keys"] == ['SCRAPPER_LINKEDIN_EMAIL', 'SCRAPPER_LINKEDIN_PWD', 'SCRAPPER_LINKEDIN_JOBS_SEARCH']


@pytest.mark.parametrize("args, invalid_field", [
    (('', 'http://url.com', 'Company', '# Markdown', False), "title"),
    (('Title', '', 'Company', '# Markdown', False), "url"),
    (('Title', 'http://url.com', '', '# Markdown', False), "company"),
    (('Title', 'http://url.com', 'Company', '', False), "markdown"),
], ids=["title", "url", "company", "markdown"])
def test_validate_logs_field_invalid(args, invalid_field):
    with captured_records(baseScrapper, "scrapper.baseScrapper") as records:
        assert validate(*args) is False
    invalid = [r for r in records if r["event"] == "job.field_invalid"]
    assert len(invalid) == 4
    assert [r["log_level"] for r in invalid] == ["error"] * 4
    assert invalid_field in [r["field"] for r in invalid]
    assert {r["url"] for r in invalid} == {args[1]}
    assert {r["debug"] for r in invalid} == {args[4]}
    assert {r["event"] for r in records} - {"job.field_invalid"} == {"debug.message"}


@pytest.mark.parametrize("url, param, expected_not_in, expected_in", [
    ("https://example.com/page?p1=v1&p2=v2", "p1", ["p1=v1"], ["p2=v2", "example.com"]),
    ("https://example.com/page?p1=v1", "p1", ["p1=v1"], ["example.com"]),
    ("https://example.com/page?p1=v1", "p2", [], ["p1=v1"]),
    ("https://example.com/page?p=1&p=2&t=r", "t", ["t=r"], ["p=1", "p=2"]),
    ("https://es.indeed.com/viewjob?jk=789&cf-turnstile-response=123", "cf-turnstile-response", ["cf-turnstile-response"], ["jk=789"])
])
def test_remove_url_parameter(url, param, expected_not_in, expected_in):
    res = removeUrlParameter(url, param)
    for item in expected_not_in: assert item not in res
    for item in expected_in: assert item in res
