import pytest
from unittest.mock import MagicMock, patch, call
from scrapper.main import main, hasArgument

@pytest.fixture
def mocks():
    with patch('scrapper.main.SeleniumService') as mock_selenium_cls, \
         patch('scrapper.main.PersistenceManager') as mock_pm_cls, \
         patch('scrapper.main.runScrapperPageUrl') as mock_run_url, \
         patch('scrapper.main.ScrapperScheduler') as mock_scheduler_cls, \
         patch('scrapper.main.getSrcPath', return_value='/src/path'):
        
        mock_selenium = mock_selenium_cls.return_value
        mock_selenium.__enter__.return_value = mock_selenium
        mock_scheduler = mock_scheduler_cls.return_value
        
        yield {
            'selenium': mock_selenium,
            'pm': mock_pm_cls.return_value,
            'run_url': mock_run_url,
            'scheduler_cls': mock_scheduler_cls,
            'scheduler': mock_scheduler
        }

def test_main_no_args(mocks):
    main(['scrapper.py'])
    mocks['selenium'].loadPage.assert_called_with('file:///src/path/scrapper/index.html')
    mocks['scheduler_cls'].assert_called_with(mocks['pm'], mocks['selenium'])
    mocks['scheduler'].runAllScrappers.assert_called_with(False, False, None)

def test_main_url_arg(mocks):
    main(['scrapper.py', 'url', 'http://example.com'])
    mocks['run_url'].assert_called_with('http://example.com')
    mocks['selenium'].loadPage.assert_not_called()

def test_main_wait_arg(mocks):
    main(['scrapper.py', 'wait'])
    mocks['scheduler'].runAllScrappers.assert_called_with(True, False, None)

def test_main_starting_arg(mocks):
    main(['scrapper.py', 'starting', 'linkedin'])
    mocks['scheduler'].runAllScrappers.assert_called_with(False, True, 'Linkedin')

def test_main_specified_scrappers(mocks):
    main(['scrapper.py', 'linkedin', 'infojobs'])
    mocks['scheduler'].runSpecifiedScrappers.assert_called_with(['linkedin', 'infojobs'])

@pytest.mark.parametrize("args, target, expected", [
    (['a', 't', 'b'], 't', True), (['a', 'b'], 't', False)
])
def test_has_argument(args, target, expected):
    assert hasArgument(args, target, lambda: None) is expected
    if expected: assert target not in args
