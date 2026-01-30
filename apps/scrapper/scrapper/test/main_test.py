import pytest
from unittest.mock import MagicMock, patch, call
from scrapper.main import main, hasArgument

@pytest.fixture
def mocks():
    with patch('scrapper.main.SeleniumService') as mock_selenium_cls, \
         patch('scrapper.main.PersistenceManager') as mock_pm_cls, \
         patch('scrapper.main.BaseExecutor') as mock_executor_cls, \
         patch('scrapper.main.ScrapperScheduler') as mock_scheduler_cls, \
         patch('scrapper.main.getSrcPath', return_value='/src/path'):
        
        mock_selenium = mock_selenium_cls.return_value
        mock_selenium.__enter__.return_value = mock_selenium
        mock_scheduler = mock_scheduler_cls.return_value
        
        yield {
            'selenium': mock_selenium,
            'pm': mock_pm_cls.return_value,
            'executor': mock_executor_cls,
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
    mocks['executor'].process_page_url.assert_called_with('http://example.com')
    mocks['selenium'].loadPage.assert_not_called()

def test_main_wait_arg(mocks):
    main(['scrapper.py', 'wait'])
    mocks['scheduler'].runAllScrappers.assert_called_with(True, False, None)

@pytest.mark.parametrize("args, should_run, expected_arg", [
    (['scrapper.py', 'starting', 'Infojobs'], True, 'Infojobs'),
    (['scrapper.py', 'starting', 'infojobs'], True, 'Infojobs'),
    (['scrapper.py', 'starting', 'infojojbs'], False, None),
    (['scrapper.py', 'starting'], False, None),
])
def test_starting(mocks, args, should_run, expected_arg):
    input_args = list(args)
    if 'starting' in input_args and len(input_args) == 2:
        with pytest.raises(SystemExit):
            main(input_args)
        return

    main(input_args)
    if should_run:
        mocks['scheduler'].runAllScrappers.assert_called_with(False, True, expected_arg)
    else:
        mocks['scheduler'].runAllScrappers.assert_not_called()

def test_main_specified_scrappers(mocks):
    main(['scrapper.py', 'linkedin', 'infojobs'])
    mocks['scheduler'].runSpecifiedScrappers.assert_called_with(['linkedin', 'infojobs'])

@pytest.mark.parametrize("args, target, expected", [
    (['a', 't', 'b'], 't', True), (['a', 'b'], 't', False)
])
def test_has_argument(args, target, expected):
    args_copy = list(args)
    result = hasArgument(args_copy, target, lambda: None)
    if expected:
        assert result == []
        assert target not in args_copy
    else:
        assert result is None
        assert args_copy == args
