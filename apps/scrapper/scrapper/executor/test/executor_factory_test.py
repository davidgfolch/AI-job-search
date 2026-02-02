import os
import glob
import pytest
from unittest.mock import MagicMock, patch
from ..executor_factory import create_executor

def _get_executor_names():
    executor_dir = os.path.dirname(os.path.dirname(__file__))
    files = glob.glob(os.path.join(executor_dir, "*Executor.py"))
    return [os.path.basename(f).replace("Executor.py", "") for f in files if "BaseExecutor" not in f]

@pytest.mark.parametrize("name", _get_executor_names())
def test_create_executor(name):
    selenium_service = MagicMock()
    persistence_manager = MagicMock()
    executor = create_executor(name, selenium_service, persistence_manager)
    assert executor.__class__.__name__ == f"{name}Executor"

def test_create_executor_invalid():
    selenium_service = MagicMock()
    persistence_manager = MagicMock()
    with pytest.raises((ValueError, KeyError)):
        create_executor('invalid', selenium_service, persistence_manager)

class TestProcessPageUrl:
    @patch('scrapper.executor.LinkedinExecutor.LinkedinExecutor.process_specific_url')
    def test_linkedin_url(self, mock_process):
        from ..executor_factory import process_page_url
        url = "https://www.linkedin.com/jobs/view/123"
        process_page_url(url)
        mock_process.assert_called_once_with(url)

    def test_unimplemented_scrapper(self):
        from ..executor_factory import process_page_url
        url = "https://www.infojobs.net/job/123"
        with pytest.raises(Exception) as excinfo:
            process_page_url(url)
        assert "Invalid scrapper web page name Infojobs, only linkedin is implemented" in str(excinfo.value)

    @patch('scrapper.executor.LinkedinExecutor.LinkedinExecutor.process_specific_url')
    def test_unknown_url(self, mock_process):
        from ..executor_factory import process_page_url
        url = "https://www.google.com"
        process_page_url(url)
        mock_process.assert_not_called()
