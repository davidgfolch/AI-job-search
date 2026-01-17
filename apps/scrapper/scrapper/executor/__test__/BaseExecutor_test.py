import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.scrapper_config import CLOSE_TAB, SCRAPPERS, TIMER
from scrapper.executor.BaseExecutor import BaseExecutor

@pytest.fixture
def mocks():
    sel = MagicMock()
    pm = MagicMock()
    return {'sel': sel, 'pm': pm}

@pytest.fixture
def run_mocks():
    names = ['Infojobs', 'Linkedin', 'Glassdoor', 'Tecnoempleo', 'Indeed']
    # Patch the actual executor modules, not inside BaseExecutor
    patchers = {name: patch(f'scrapper.executor.{name}Executor.{name}Executor') for name in names}
    yield {name: p.start() for name, p in patchers.items()}
    for p in patchers.values(): p.stop()

class TestExecutor:
    @pytest.mark.parametrize("name", ['Infojobs'])
    def test_create_executor(self, mocks, run_mocks, name):
        mock_executor_cls = run_mocks[name]
        
        executor = BaseExecutor.create(name.lower(), mocks['sel'], mocks['pm'])
        
        mock_executor_cls.assert_called_with(mocks['sel'], mocks['pm'])

    @pytest.mark.parametrize("name", ['Infojobs'])
    def test_execute_preload(self, mocks, run_mocks, name):
        mock_executor_cls = run_mocks[name]
        mock_instance = mock_executor_cls.return_value
        props = {}
        
        executor = BaseExecutor.create(name.lower(), mocks['sel'], mocks['pm'])
        executor.execute_preload(props)
        
        mock_instance.execute_preload.assert_called_with(props)

    @pytest.mark.parametrize("name", ['Infojobs'])
    def test_execute(self, mocks, run_mocks, name):
        mock_executor_cls = run_mocks[name]
        mock_instance = mock_executor_cls.return_value
        props = {}
        
        executor = BaseExecutor.create(name.lower(), mocks['sel'], mocks['pm'])
        executor.execute(props)
        
        mock_instance.execute.assert_called_with(props)


class TestProcessPageUrl:
    def test_linkedin_url(self, mocks):
        url = "https://www.linkedin.com/jobs/view/123"
        with patch('scrapper.executor.LinkedinExecutor.LinkedinExecutor.process_specific_url') as mock_process:
            BaseExecutor.process_page_url(url)
            mock_process.assert_called_once_with(url)

    def test_unimplemented_scrapper(self):
        url = "https://www.infojobs.net/job/123"
        with pytest.raises(Exception) as excinfo:
            BaseExecutor.process_page_url(url)
        assert "Invalid scrapper web page name Infojobs, only linkedin is implemented" in str(excinfo.value)

    def test_unknown_url(self):
        url = "https://www.google.com"
        with patch('scrapper.executor.LinkedinExecutor.LinkedinExecutor.process_specific_url') as mock_process:
            BaseExecutor.process_page_url(url)
            mock_process.assert_not_called()
