import pytest

from unittest.mock import patch, MagicMock
from scrapper.main import SCRAPPERS, runAllScrappers, runSpecifiedScrappers


@pytest.fixture
def mock_scrappers():
    with patch.dict(SCRAPPERS, {
        'Infojobs': {'function': MagicMock(), 'timer': '2h'},
        'Linkedin': {'function': MagicMock(), 'timer': '1h'},
        'Glassdoor': {'function': MagicMock(), 'timer': '3h'},
        'Tecnoempleo': {'function': MagicMock(), 'timer': '2h'},
        'Indeed': {'function': MagicMock(), 'timer': '3h', 'ignoreAutoRun': True},
    }):
        yield


@pytest.fixture
def mock_selenium():
    # Patch the module-level seleniumUtil object used in main so
    # calls like seleniumUtil.tab(...) don't fail during tests.
    with patch('scrapper.main.seleniumUtil', MagicMock()):
        yield


def test_runAllScrappers(mock_scrappers, mock_selenium):
    with patch('scrapper.main.consoleTimer', return_value=None), \
            patch('scrapper.main.getDatetimeNow', return_value=0), \
            patch('scrapper.main.getSeconds', return_value=0):
        runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loop=False)
        for name, properties in SCRAPPERS.items():
            scrapper = properties['function']
            if not scrapper.get('ignoreAutoRun', False):
                scrapper.assert_called_once()


def test_runAllScrappers_with_wait(mock_scrappers, mock_selenium):
    with patch('scrapper.main.consoleTimer', return_value=None), \
            patch('scrapper.main.getDatetimeNow', return_value=0), \
            patch('scrapper.main.getSeconds', return_value=0):
        runAllScrappers(waitBeforeFirstRuns=True, starting=False, startingAt=None, loop=False)
        for name, properties in SCRAPPERS.items():
            scrapper = properties['function']
            if not scrapper.get('ignoreAutoRun', False):
                scrapper['function'].assert_called_once()


def test_runSpecifiedScrappers(mock_scrappers, mock_selenium):
    runSpecifiedScrappers(['Infojobs', 'Linkedin'])
    # runSpecifiedScrappers calls preload (True) and then execute (False),
    # so the function should be called twice for each scrapper.
    assert SCRAPPERS['Infojobs']['function'].call_count == 2
    assert SCRAPPERS['Linkedin']['function'].call_count == 2


def test_runSpecifiedScrappers_invalid_name(mock_scrappers, mock_selenium):
    with patch('sys.argv', ['scrapper/main.py', 'InvalidScrapper']), \
            patch('scrapper.main.red',
                  return_value='Invalid scrapper web page name InvalidScrapper'), \
            patch('scrapper.main.yellow',
                  return_value='Available web page scrapper names: dict_keys([\'Infojobs\', \'Linkedin\', \'Glassdoor\', \'Tecnoempleo\', \'Indeed\'])'):
        runSpecifiedScrappers(['InvalidScrapper'])
        for scrapper in SCRAPPERS.values():
            scrapper['function'].assert_not_called()
