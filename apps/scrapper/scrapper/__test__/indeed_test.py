import pytest
from unittest.mock import MagicMock, patch
from scrapper.indeed import run, search_jobs, process_row, load_and_process_row
from scrapper.navigator.indeedNavigator import IndeedNavigator
from scrapper.services.IndeedService import IndeedService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil


@pytest.fixture
def mock_selenium():
    return MagicMock(spec=SeleniumService)


@pytest.fixture
def mock_mysql():
    return MagicMock(spec=MysqlUtil)


@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)


@pytest.fixture
def mock_navigator():
    return MagicMock(spec=IndeedNavigator)


@pytest.fixture
def mock_service():
    return MagicMock(spec=IndeedService)


class TestIndeedScrapper:
    def test_run_preload_page(self, mock_selenium):
        with (
            patch("scrapper.indeed.JOBS_SEARCH", "python developer"),
            patch("scrapper.indeed.IndeedNavigator") as mock_nav_class,
            patch("scrapper.indeed.IndeedService") as mock_service_class,
        ):
            mock_nav_instance = mock_nav_class.return_value

            run(mock_selenium, preloadPage=True)

            # Verify that login is called and search is not called
            mock_nav_instance.login.assert_called_once()
            mock_nav_instance.search.assert_not_called()
            mock_service_class.assert_not_called()

    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager):
        with (
            patch("scrapper.indeed.JOBS_SEARCH", "python"),
            patch("scrapper.indeed.MysqlUtil") as mock_mysql_class,
            patch("scrapper.indeed.IndeedNavigator") as mock_nav_class,
            patch("scrapper.indeed.IndeedService") as mock_service_class,
            patch("scrapper.indeed.search_jobs") as mock_search_jobs,
        ):
            mock_mysql_instance = MagicMock(spec=MysqlUtil)
            mock_mysql_class.return_value.__enter__.return_value = mock_mysql_instance

            mock_persistence_manager.get_state.return_value = {}

            run(
                mock_selenium,
                preloadPage=False,
                persistenceManager=mock_persistence_manager,
            )

            assert mock_search_jobs.called
            mock_persistence_manager.get_state.assert_called_with("Indeed")
            mock_persistence_manager.finalize_scrapper.assert_called_with("Indeed")

    def test_get_job_id(self):
        # Testing IndeedService method
        service = IndeedService(MagicMock(), MagicMock())
        url = "https://es.indeed.com/viewjob?jk=1234567890&other=param"
        assert service.get_job_id(url) == "1234567890"

        url2 = "https://es.indeed.com/pagead/clk?mo=r&ad=...&jk=0987654321&..."
        assert service.get_job_id(url2) == "0987654321"

    def test_search_jobs_pagination(self):
        # Setup mocks for search_jobs
        # mocking global navigator variable in indeed module

        with (
            patch("scrapper.indeed.IndeedNavigator") as mock_nav_class,
            patch("scrapper.indeed.IndeedService") as mock_service_class,
            patch("scrapper.indeed.navigator") as mock_navigator,
            patch("scrapper.indeed.service") as mock_service,
            patch("scrapper.indeed.load_and_process_row", return_value=True) as mock_process_row,
            patch("scrapper.indeed.summarize"),
            patch("scrapper.indeed.sleep"),
        ):
            # Configure navigator mock
            mock_navigator.click_next_page.side_effect = [True, False]

            # We need to manually inject these if they are not set by run()
            # or we can just mock what search_jobs uses.
            # search_jobs uses global 'navigator' and 'service'

            search_jobs("python", startPage=1)

            # 16 jobs per page * 2 pages = 32 calls
            assert mock_process_row.call_count == 32

    def test_process_row_insert(self):
        # Testing process_row which now delegates to Service and uses Navigator

        mock_navigator = MagicMock(spec=IndeedNavigator)
        mock_service = MagicMock(spec=IndeedService)

        # Setup navigator return values
        mock_navigator.get_job_data.return_value = (
            "Job Title",
            "Company Name",
            "Location",
            "<html>...</html>",
        )
        mock_navigator.check_easy_apply.return_value = False

        # Setup service return values
        mock_service.process_job.return_value = True

        with (
            patch("scrapper.indeed.navigator", mock_navigator),
            patch("scrapper.indeed.service", mock_service),
        ):
            result = process_row("http://job.url")

            assert result is True
            mock_navigator.get_job_data.assert_called_once()
            mock_service.process_job.assert_called_once_with(
                "Job Title",
                "Company Name",
                "Location",
                "http://job.url",
                "<html>...</html>",
                False,
            )

    def test_service_process_job_insert(self, mock_mysql):
        # Test the Service logic specifically
        service = IndeedService(mock_mysql, MagicMock())
        service.set_debug(False)

        with (
            patch("scrapper.services.IndeedService.validate", return_value=True),
            patch(
                "scrapper.services.IndeedService.htmlToMarkdown",
                return_value="Description",
            ),
            patch("scrapper.services.IndeedService.mergeDuplicatedJobs"),
        ):
            mock_mysql.insert.return_value = 1
            mock_mysql.fetchOne.return_value = None

            result = service.process_job(
                "Title", "Company", "Location", "http://url?jk=123", "<html/>", False
            )

            assert result is True
            mock_mysql.insert.assert_called_once()
            args = mock_mysql.insert.call_args[0]
            assert "123" == args[0][0]
            assert "Title" == args[0][1]

    def test_service_process_job_validation_fail(self, mock_mysql):
        service = IndeedService(mock_mysql, MagicMock())
        service.set_debug(False)

        with (
            patch("scrapper.services.IndeedService.validate", return_value=False),
            patch(
                "scrapper.services.IndeedService.htmlToMarkdown",
                return_value="Description",
            ),
        ):
            mock_mysql.fetchOne.return_value = None
            result = service.process_job(
                "Title", "Company", "Location", "http://url?jk=123", "<html/>", False
            )

            assert result is False
            mock_mysql.insert.assert_not_called()

    def test_post_process_markdown(self):
        service = IndeedService(MagicMock(), MagicMock())
        md = "Check [this link](/ofertas-trabajo/123) for details."
        processed = service.post_process_markdown(md)
        assert "this link" in processed
        assert "/ofertas-trabajo/123" not in processed
