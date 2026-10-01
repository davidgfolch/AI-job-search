import pytest
from unittest.mock import MagicMock, patch
from scrapper.executor.InfojobsExecutor import InfojobsExecutor
from scrapper.navigator.infojobsNavigator import InfojobsNavigator
from scrapper.services.InfojobsService import InfojobsService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from commonlib.sql.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_selenium():
    mock = MagicMock(spec=SeleniumService)
    mock.driverUtil = MagicMock()
    mock.driverUtil.useUndetected = False
    return mock

@pytest.fixture
def mock_mysql():
    return MagicMock(spec=MysqlUtil)

@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.executor.InfojobsExecutor.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestInfojobsExecutor:

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        with patch('scrapper.executor.InfojobsExecutor.InfojobsNavigator') as mock_nav_class:
            mock_nav = mock_nav_class.return_value
            executor = InfojobsExecutor(mock_selenium, mock_persistence_manager, False)
            executor.run(preload_page=True)
            mock_nav.load_search_page.assert_called_once()
            if not mock_selenium.driverUtil.useUndetected:
                mock_nav.security_filter.assert_called_once()
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.executor.InfojobsExecutor.InfojobsNavigator'), \
             patch('scrapper.executor.InfojobsExecutor.InfojobsService') as mock_service_cls, \
             patch('scrapper.executor.BaseExecutor.MysqlUtil'), \
             patch.object(InfojobsExecutor, '_process_keyword') as mock_process_keyword:
            
            mock_service = mock_service_cls.return_value
            mock_service.should_skip_keyword.return_value = (False, 1)

            executor = InfojobsExecutor(mock_selenium, mock_persistence_manager, False)
            executor.run(preload_page=False)
            assert mock_process_keyword.called
            mock_persistence_manager.finalize_scrapper.assert_called_with('Infojobs')

    def test_process_keyword_flow(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch.object(InfojobsExecutor, '_load_and_process_row', return_value=False) as mock_row, \
             patch('scrapper.executor.InfojobsExecutor.InfojobsNavigator') as mock_nav_class:
            
            executor = InfojobsExecutor(mock_selenium, mock_persistence_manager, False)
            executor.service = MagicMock()
            mock_nav = executor.navigator
            mock_nav.load_filtered_search_results.return_value = True
            mock_nav.get_total_results.return_value = 10
            mock_nav.fast_forward_page.return_value = 1
            mock_nav.click_next_page.return_value = False
            
            executor._process_keyword("python", start_page=1)
            
            mock_nav.load_search_page.assert_called()
            mock_nav.load_filtered_search_results.assert_called_with('python')
            assert mock_row.call_count == 10

class TestInfojobsService:
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return InfojobsService(mock_mysql, mock_persistence_manager, False)

    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.infojobs.net/of-1234567890?other=param", "1234567890"),
        ("https://www.infojobs.net/of-0987654321", "0987654321"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id

    def test_job_exists_in_db(self, service, mock_mysql):
        mock_mysql.fetchOne.return_value = {"id": 1}
        job_id, exists = service.job_exists_in_db("https://www.infojobs.net/of-123")
        assert job_id == "123"
        assert exists is True

    def test_process_job_valid(self, service, mock_mysql):
        with patch('scrapper.services.InfojobsService.htmlToMarkdown', return_value="Markdown"), \
             patch('scrapper.services.InfojobsService.validate', return_value=True), \
             patch('scrapper.services.InfojobsService.find_last_duplicated'):
             
             mock_mysql.insert.return_value = 1
             result = service.process_job("Title", "Company", "Location", "https://www.infojobs.net/of-123", "<html>")
             
             assert result is True
             mock_mysql.insert.assert_called_once()

@pytest.fixture(autouse=True)
def silence_console():
    with patch('scrapper.executor.InfojobsExecutor.baseScrapper.printPage'), \
         patch('scrapper.executor.InfojobsExecutor.baseScrapper.summarize'):
        yield


class TestLoadRow:
    def test_does_not_scroll_for_the_first_rows(self, infojobs_executor, infojobs_navigator):
        infojobs_executor.service.job_exists_in_db.return_value = (7, False)
        infojobs_navigator.get_job_url.return_value = 'https://infojobs/job/1'
        assert infojobs_executor._load_row(0) == 'https://infojobs/job/1'
        infojobs_navigator.scroll_jobs_list.assert_not_called()
        infojobs_navigator.click_job_link.assert_called_once()

    def test_scrolls_before_reading_a_row_below_the_fold(self, infojobs_executor, infojobs_navigator):
        infojobs_executor.service.job_exists_in_db.return_value = (7, False)
        infojobs_navigator.get_job_url.return_value = 'https://infojobs/job/3'
        assert infojobs_executor._load_row(5) == 'https://infojobs/job/3'
        infojobs_navigator.scroll_jobs_list.assert_called_once_with(5)

    def test_returns_none_when_the_scroll_fails(self, infojobs_executor, infojobs_navigator):
        infojobs_navigator.scroll_jobs_list.side_effect = RuntimeError('stale element')
        assert infojobs_executor._load_row(9) is None
        infojobs_navigator.get_job_link_element.assert_not_called()

    def test_returns_true_without_clicking_when_the_job_is_already_stored(self, infojobs_executor, infojobs_navigator):
        infojobs_executor.service.job_exists_in_db.return_value = (7, True)
        assert infojobs_executor._load_row(0) is True
        infojobs_navigator.click_job_link.assert_not_called()


class TestProcessAndLoadRow:
    def test_process_row_forwards_the_navigator_payload_to_the_service(self, infojobs_executor, infojobs_navigator):
        infojobs_navigator.get_job_data.return_value = ('title', 'company', 'location', 'extra', '<html>')
        infojobs_executor.service.process_job.return_value = True
        assert infojobs_executor._process_row('https://infojobs/job/1') is True
        infojobs_executor.service.process_job.assert_called_once_with('title', 'company', 'location', 'https://infojobs/job/1', '<html>')

    @pytest.mark.parametrize("loaded", [True, None], ids=["already_stored", "scroll_failed"])
    def test_load_and_process_row_short_circuits_on_a_non_url(self, infojobs_executor, loaded):
        with patch.object(InfojobsExecutor, '_load_row', return_value=loaded):
            assert infojobs_executor._load_and_process_row(0) == loaded
        infojobs_executor.service.process_job.assert_not_called()

    def test_load_and_process_row_returns_false_when_validation_fails(self, infojobs_executor, infojobs_navigator):
        infojobs_navigator.get_url.return_value = infojobs_executor.list_url
        with patch.object(InfojobsExecutor, '_load_row', return_value='https://infojobs/job/1'), \
             patch.object(InfojobsExecutor, '_process_row', return_value=False):
            assert infojobs_executor._load_and_process_row(0) is False

    def test_load_and_process_row_goes_back_after_leaving_the_list(self, infojobs_executor, infojobs_navigator):
        infojobs_navigator.get_url.return_value = 'https://www.infojobs.net/detail/1'
        with patch.object(InfojobsExecutor, '_load_row', return_value='https://infojobs/job/1'), \
             patch.object(InfojobsExecutor, '_process_row', return_value=True):
            assert infojobs_executor._load_and_process_row(0) is False
        infojobs_navigator.go_back.assert_called_once()


class TestKeywordPagination:
    def _stub_search(self, infojobs_navigator, total_results, click_next_page=True):
        infojobs_navigator.load_filtered_search_results.return_value = True
        infojobs_navigator.get_total_results.return_value = total_results
        infojobs_navigator.fast_forward_page.return_value = 1
        infojobs_navigator.click_next_page.return_value = click_next_page
        infojobs_navigator.wait_until_page_is_loaded = MagicMock()
        infojobs_navigator.get_url.return_value = 'https://www.infojobs.net/ofertas-trabajo'

    def test_returns_early_when_the_filtered_search_returns_nothing(self, infojobs_executor, infojobs_navigator):
        infojobs_navigator.load_filtered_search_results.return_value = False
        infojobs_executor._process_keyword('python', 1)
        infojobs_navigator.get_total_results.assert_not_called()

    def test_advances_and_persists_the_page_when_more_results_remain(self, infojobs_executor, infojobs_navigator):
        self._stub_search(infojobs_navigator, 66)
        with patch.object(InfojobsExecutor, '_load_and_process_row', return_value=False):
            infojobs_executor._process_keyword('python', 1)
        assert infojobs_navigator.click_next_page.call_count == 2
        infojobs_navigator.wait_until_page_is_loaded.assert_called()
        assert infojobs_executor.service.update_state.call_args_list[-1].args == ('python', 3)

    def test_stops_when_there_is_no_next_page(self, infojobs_executor, infojobs_navigator):
        self._stub_search(infojobs_navigator, 66, click_next_page=False)
        with patch.object(InfojobsExecutor, '_load_and_process_row', return_value=False):
            infojobs_executor._process_keyword('python', 1)
        infojobs_navigator.click_next_page.assert_called_once()
        infojobs_executor.service.update_state.assert_not_called()

    def test_stops_keyword_processing_after_pages_without_new_jobs(self, infojobs_executor, infojobs_navigator):
        self._stub_search(infojobs_navigator, 66)
        with patch.object(InfojobsExecutor, '_load_and_process_row', return_value=True):
            infojobs_executor._process_keyword('python', 1)
        assert infojobs_navigator.click_next_page.call_count == 2
