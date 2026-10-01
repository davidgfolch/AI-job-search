"""Shared fixtures for the executor tests.

Kept out of the test modules so each `<source>_test.py` stays focused: the architecture
tests enforce a 1:1 `<source>_test.py` -> `<source>.py` correspondence, which forbids
splitting a suite across several files.
"""
import pytest
from unittest.mock import MagicMock, patch
from scrapper.executor.BaseExecutor import BaseExecutor
from scrapper.executor.IndeedExecutor import IndeedExecutor
from scrapper.executor.InfojobsExecutor import InfojobsExecutor
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager


@pytest.fixture
def selenium_service():
    mock = MagicMock(spec=SeleniumService)
    mock.configure_mock(driverUtil=MagicMock(useUndetected=False))
    return mock


@pytest.fixture
def infojobs_executor(selenium_service):
    with patch('scrapper.executor.InfojobsExecutor.baseScrapper.printPage'), \
         patch('scrapper.executor.InfojobsExecutor.baseScrapper.summarize'), \
         patch('scrapper.executor.InfojobsExecutor.getAndCheckEnvVars', return_value=('a@b.c', 'pwd', 'python')), \
         patch('scrapper.executor.InfojobsExecutor.InfojobsNavigator'), \
         patch('scrapper.executor.InfojobsExecutor.InfojobsService') as service_cls, \
         patch('scrapper.executor.BaseExecutor.MysqlUtil'):
        sut = InfojobsExecutor(selenium_service, MagicMock(spec=PersistenceManager), False)
        sut.service = service_cls.return_value
        yield sut


@pytest.fixture
def infojobs_navigator(infojobs_executor):
    return infojobs_executor.navigator


@pytest.fixture
def indeed_executor(selenium_service):
    with patch('scrapper.executor.IndeedExecutor.sleep'), \
         patch('scrapper.executor.IndeedExecutor.baseScrapper.printPage'), \
         patch('scrapper.executor.IndeedExecutor.baseScrapper.summarize'), \
         patch('scrapper.executor.IndeedExecutor.getAndCheckEnvVars', return_value=('a@b.c', 'pwd', 'python')), \
         patch('scrapper.executor.IndeedExecutor.IndeedNavigator'), \
         patch('scrapper.executor.IndeedExecutor.IndeedService') as service_cls, \
         patch('scrapper.executor.BaseExecutor.MysqlUtil'):
        sut = IndeedExecutor(selenium_service, MagicMock(spec=PersistenceManager), False)
        sut.service = service_cls.return_value
        yield sut


@pytest.fixture
def indeed_navigator(indeed_executor):
    return indeed_executor.navigator


class StubKeywordExecutor(BaseExecutor):
    """Concrete BaseExecutor subclass that skips the browser bootstrap entirely."""

    def __init__(self, persistence_manager, service):
        self.persistence_manager = persistence_manager
        self.service = service
        self.site_name = "STUB"
        self.debug = False
        self.jobs_search = 'python,java'

    def _create_service(self, mysql):
        return self.service

    def _process_keyword(self, keyword, start_page):
        pass


@pytest.fixture
def stub_executor():
    return StubKeywordExecutor


@pytest.fixture
def persistence():
    manager = MagicMock()
    manager.get_state.return_value = {}
    return manager


@pytest.fixture
def process_keyword():
    with patch.object(StubKeywordExecutor, '_process_keyword') as mock_process:
        yield mock_process


@pytest.fixture(autouse=True)
def base_mysql():
    with patch('scrapper.executor.BaseExecutor.MysqlUtil'):
        yield()
