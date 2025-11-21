import pytest
from unittest.mock import patch
from scrapper.baseScrapper import (
    getAndCheckEnvVars, htmlToMarkdown, removeInvalidScapes,
    removeLinks, validate, debug, join, printScrapperTitle, printPage
)

class TestGetAndCheckEnvVars:
    @patch('scrapper.baseScrapper.getEnv')
    def test_all_vars_present(self, mockGetEnv):
        mockGetEnv.side_effect = ['test@email.com', 'password', 'python developer']
        email, pwd, search = getAndCheckEnvVars('LINKEDIN')
        assert email == 'test@email.com'
        assert pwd == 'password'
        assert search == 'python developer'
    
    @patch('scrapper.baseScrapper.getEnv')
    def test_fallback_to_generic_search(self, mockGetEnv):
        mockGetEnv.side_effect = ['test@email.com', 'password', None, 'generic search']
        email, pwd, search = getAndCheckEnvVars('LINKEDIN')
        assert search == 'generic search'
    
    @patch('scrapper.baseScrapper.getEnv')
    def test_missing_email_exits(self, mockGetEnv):
        mockGetEnv.side_effect = [None, 'password', 'search']
        with pytest.raises(SystemExit):
            getAndCheckEnvVars('LINKEDIN')
    
    @patch('scrapper.baseScrapper.getEnv')
    def test_missing_password_exits(self, mockGetEnv):
        mockGetEnv.side_effect = ['test@email.com', None, 'search']
        with pytest.raises(SystemExit):
            getAndCheckEnvVars('LINKEDIN')
    
    @patch('scrapper.baseScrapper.getEnv')
    def test_missing_search_exits(self, mockGetEnv):
        mockGetEnv.side_effect = ['test@email.com', 'password', None, None]
        with pytest.raises(SystemExit):
            getAndCheckEnvVars('LINKEDIN')

class TestHtmlToMarkdown:
    def test_simple_html(self):
        html = '<p>Hello World</p>'
        md = htmlToMarkdown(html)
        assert 'Hello World' in md
    
    def test_html_with_links(self):
        html = '<a href="http://test.com">Link</a>'
        md = htmlToMarkdown(html)
        assert 'Link' in md
    
    def test_html_with_br(self):
        html = '<p>Line1<br>Line2</p>'
        md = htmlToMarkdown(html)
        assert 'Line1' in md
        assert 'Line2' in md
    
    def test_html_with_lists(self):
        html = '<ul><li>Item1</li><li>Item2</li></ul>'
        md = htmlToMarkdown(html)
        assert 'Item1' in md
        assert 'Item2' in md
    
    def test_removes_invalid_escapes(self):
        html = '<p>Price: \\$100</p>'
        md = htmlToMarkdown(html)
        assert '$100' in md

class TestRemoveInvalidScapes:
    def test_removes_dollar_escape(self):
        text = 'Price: \\$100'
        result = removeInvalidScapes(text)
        assert result == 'Price: $100'
    
    def test_removes_backslashes(self):
        text = 'Test\\nText\\tHere'
        result = removeInvalidScapes(text)
        assert '\\' not in result or '\\u' in result
    
    def test_preserves_unicode_escapes(self):
        text = 'Unicode: \\u0041'
        result = removeInvalidScapes(text)
        assert '\\u0041' in result

class TestRemoveLinks:
    def test_removes_markdown_links(self):
        text = 'Check [this link](http://example.com) for more'
        result = removeLinks(text)
        assert 'this link' in result
        assert 'http://example.com' not in result
    
    def test_multiple_links(self):
        text = '[Link1](url1) and [Link2](url2)'
        result = removeLinks(text)
        assert 'Link1' in result
        assert 'Link2' in result
        assert 'url1' not in result
        assert 'url2' not in result
    
    def test_no_links(self):
        text = 'Plain text without links'
        result = removeLinks(text)
        assert result == text

class TestValidate:
    def test_all_fields_valid(self):
        result = validate('Title', 'http://url.com', 'Company', '# Markdown', False)
        assert result is True
    
    def test_empty_title(self):
        result = validate('', 'http://url.com', 'Company', '# Markdown', False)
        assert result is False
    
    def test_empty_url(self):
        result = validate('Title', '', 'Company', '# Markdown', False)
        assert result is False
    
    def test_empty_company(self):
        result = validate('Title', 'http://url.com', '', '# Markdown', False)
        assert result is False
    
    def test_empty_markdown(self):
        result = validate('Title', 'http://url.com', 'Company', '', False)
        assert result is False
    
    def test_whitespace_only_fields(self):
        result = validate('   ', 'http://url.com', 'Company', '# Markdown', False)
        assert result is False

class TestDebug:
    def test_debug_disabled_no_exception(self):
        with patch('builtins.print') as mockPrint:
            debug(False, 'Test message', exception=False)
            mockPrint.assert_called()
    
    def test_debug_disabled_with_exception(self):
        with patch('builtins.print') as mockPrint:
            debug(False, 'Test message', exception=True)
            assert mockPrint.call_count >= 2
    
    def test_debug_enabled_no_exception(self):
        with patch('builtins.input', return_value=''):
            debug(True, 'Test message', exception=False)
    
    def test_debug_enabled_with_exception(self):
        with patch('builtins.input', return_value=''), \
             patch('builtins.print'):
            debug(True, 'Test message', exception=True)

class TestJoin:
    def test_join_multiple_strings(self):
        result = join('Hello', ' ', 'World')
        assert result == 'Hello World'
    
    def test_join_empty_strings(self):
        result = join('', '', '')
        assert result == ''
    
    def test_join_single_string(self):
        result = join('Single')
        assert result == 'Single'

class TestPrintScrapperTitle:
    @patch('scrapper.baseScrapper.printHR')
    @patch('scrapper.baseScrapper.getDatetimeNowStr')
    def test_preload_mode(self, mockGetDatetime, mockPrintHR):
        mockGetDatetime.return_value = '2025-01-01 12:00:00'
        with patch('builtins.print') as mockPrint:
            printScrapperTitle('LinkedIn', True)
            mockPrint.assert_called()
            mockPrintHR.assert_called()
    
    @patch('scrapper.baseScrapper.printHR')
    @patch('scrapper.baseScrapper.getDatetimeNowStr')
    def test_normal_mode(self, mockGetDatetime, mockPrintHR):
        mockGetDatetime.return_value = '2025-01-01 12:00:00'
        with patch('builtins.print') as mockPrint:
            printScrapperTitle('LinkedIn', False)
            mockPrint.assert_called()
            mockPrintHR.assert_called()

class TestPrintPage:
    @patch('scrapper.baseScrapper.printHR')
    @patch('scrapper.baseScrapper.getDatetimeNowStr')
    def test_print_page(self, mockGetDatetime, mockPrintHR):
        mockGetDatetime.return_value = '2025-01-01 12:00:00'
        with patch('builtins.print') as mockPrint:
            printPage('LinkedIn', 1, 10, 'python developer')
            mockPrint.assert_called()
            mockPrintHR.assert_called()
