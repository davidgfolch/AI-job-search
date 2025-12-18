import pytest
from unittest.mock import MagicMock, patch, call
from scrapper.main import main, hasArgument

@pytest.fixture
def mocks():
    with patch('scrapper.main.SeleniumService') as mock_selenium_cls, \
         patch('scrapper.main.PersistenceManager') as mock_pm_cls, \
         patch('scrapper.main.ScrapperContainer') as mock_container_cls, \
         patch('scrapper.main.runScrapperPageUrl') as mock_run_url, \
         patch('scrapper.main.runAllScrappers') as mock_run_all, \
         patch('scrapper.main.runSpecifiedScrappers') as mock_run_specified, \
         patch('scrapper.main.getSrcPath', return_value='/src/path'):
        
        mock_selenium = mock_selenium_cls.return_value
        mock_selenium.__enter__.return_value = mock_selenium
        
        yield {
            'selenium': mock_selenium,
            'pm': mock_pm_cls.return_value,
            'container': mock_container_cls.return_value,
            'run_url': mock_run_url,
            'run_all': mock_run_all,
            'run_specified': mock_run_specified
        }

def test_main_no_args(mocks):
    main(['scrapper.py'])
    mocks['selenium'].loadPage.assert_called_with('file:///src/path/scrapper/index.html')
    mocks['run_all'].assert_called_with(False, False, None, mocks['pm'], mocks['selenium'], mocks['container'])

def test_main_url_arg(mocks):
    main(['scrapper.py', 'url', 'http://example.com'])
    mocks['run_url'].assert_called_with('http://example.com')
    mocks['selenium'].loadPage.assert_not_called()

def test_main_wait_arg(mocks):
    main(['scrapper.py', 'wait'])
    mocks['run_all'].assert_called_with(True, False, None, mocks['pm'], mocks['selenium'], mocks['container'])

def test_main_starting_arg(mocks):
    main(['scrapper.py', 'starting', 'linkedin'])
    mocks['run_all'].assert_called_with(False, True, 'Linkedin', mocks['pm'], mocks['selenium'], mocks['container'])

def test_main_specified_scrappers(mocks):
    main(['scrapper.py', 'linkedin', 'infojobs'])
    mocks['run_specified'].assert_called_with(['linkedin', 'infojobs'], mocks['pm'], mocks['selenium'], mocks['container'])

@pytest.mark.parametrize("args, target, expected", [
    (['a', 't', 'b'], 't', True), (['a', 'b'], 't', False)
])
def test_has_argument(args, target, expected):
    assert hasArgument(args, target, lambda: None) is expected
    if expected: assert target not in args
