import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.baseScrapper import (
    getAndCheckEnvVars, htmlToMarkdown, removeInvalidScapes,
    removeLinks, validate, debug, join, printScrapperTitle, printPage, removeUrlParameter
)

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

class TestDebug:
    @pytest.mark.parametrize("debug_mode, exception, input_se, print_count", [
        (False, False, None, 1),
        (False, True, None, 2),
        (True, False, [''], 0),
        (True, True, [''], 0) # Mock print separately if needed
    ])
    def test_debug(self, debug_mode, exception, input_se, print_count):
        with patch('builtins.print') as mp, patch('builtins.input', side_effect=input_se or []):
            debug(debug_mode, 'Msg', exception=exception)
            if not debug_mode: 
                assert mp.call_count >= print_count

@pytest.mark.parametrize("strings, expected", [
    (('Hello', ' ', 'World'), 'Hello World'),
    (('', '', ''), ''),
    (('Single',), 'Single')
])
def test_join(strings, expected):
    assert join(*strings) == expected

@pytest.mark.parametrize("preload", [True, False])
@patch('scrapper.core.baseScrapper.printHR')
@patch('scrapper.core.baseScrapper.getDatetimeNowStr', return_value='2025-01-01')
def test_print_scrapper_title(mock_date, mock_hr, preload):
    with patch('builtins.print') as mock_print:
        printScrapperTitle('LinkedIn', preload)
        mock_print.assert_called()
        mock_hr.assert_called()

@patch('scrapper.core.baseScrapper.printHR')
@patch('scrapper.core.baseScrapper.getDatetimeNowStr', return_value='2025-01-01')
def test_print_page(mock_date, mock_hr):
    with patch('builtins.print') as mock_print:
        printPage('LinkedIn', 1, 10, 'python developer')
        mock_print.assert_called()
        mock_hr.assert_called()

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
