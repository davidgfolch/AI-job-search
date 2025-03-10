import pytest
from unittest.mock import patch, MagicMock

from ai_job_search.scrapper_main import (
    SCRAPPERS, runAllScrappers, runSpecifiedScrappers)


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
    with patch('ai_job_search.scrapper_main.SeleniumUtil', MagicMock):
        yield


def test_runAllScrappers(mock_scrappers):
    with patch('ai_job_search.scrapper_main.consoleTimer', return_value=None), \
            patch('ai_job_search.scrapper_main.getDatetimeNow', return_value=0), \
            patch('ai_job_search.scrapper_main.getSeconds', return_value=0):
        runAllScrappers(waitBeforeFirstRuns=False,
                        starting=False, startingAt=None, loop=False)
        for scrapper in SCRAPPERS.values():
            if not scrapper.get('ignoreAutoRun', False):
                scrapper['function'].assert_called_once()


def test_runAllScrappers_with_wait(mock_scrappers):
    with patch('ai_job_search.scrapper_main.consoleTimer', return_value=None), \
            patch('ai_job_search.scrapper_main.getDatetimeNow', return_value=0), \
            patch('ai_job_search.scrapper_main.getSeconds', return_value=0):
        runAllScrappers(waitBeforeFirstRuns=True,
                        starting=False, startingAt=None, loop=False)
        for scrapper in SCRAPPERS.values():
            if not scrapper.get('ignoreAutoRun', False):
                scrapper['function'].assert_called_once()


def test_runSpecifiedScrappers(mock_scrappers):
    runSpecifiedScrappers(['Infojobs', 'Linkedin'])
    SCRAPPERS['Infojobs']['function'].assert_called_once()
    SCRAPPERS['Linkedin']['function'].assert_called_once()


def test_runSpecifiedScrappers_invalid_name(mock_scrappers):
    with patch('sys.argv', ['scrapper_main.py', 'InvalidScrapper']), \
            patch('ai_job_search.scrapper_main.red',
                  return_value='Invalid scrapper web page name InvalidScrapper'), \
            patch('ai_job_search.scrapper_main.yellow',
                  return_value='Available web page scrapper names: dict_keys([\'Infojobs\', \'Linkedin\', \'Glassdoor\', \'Tecnoempleo\', \'Indeed\'])'):
        runSpecifiedScrappers(['InvalidScrapper'])
        for scrapper in SCRAPPERS.values():
            scrapper['function'].assert_not_called()
