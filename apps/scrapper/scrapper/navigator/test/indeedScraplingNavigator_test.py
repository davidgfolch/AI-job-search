import pytest
from unittest.mock import MagicMock
from scrapper.navigator.indeedScraplingNavigator import IndeedScraplingNavigator
from scrapper.navigator.test.indeedScraplingNavigator_fixtures import (
    MockSelector, _make_navigator, _new_dom_page, create_mock_scrapling_service,
)


class TestIndeedScraplingNavigator:
    def test_init_without_proxies(self):
        mock_service = create_mock_scrapling_service()
        with pytest.MonkeyPatch.context() as m:
            m.setattr("scrapper.navigator.indeedScraplingNavigator.ScraplingService", lambda proxies, debug: mock_service)
            navigator = IndeedScraplingNavigator(proxies=[], debug=False)
            assert navigator.scrapling_service is mock_service

    def test_init_with_proxies(self):
        mock_service = create_mock_scrapling_service()
        with pytest.MonkeyPatch.context() as m:
            m.setattr("scrapper.navigator.indeedScraplingNavigator.ScraplingService", lambda proxies, debug: mock_service)
            navigator = IndeedScraplingNavigator(proxies=["http://localhost"], debug=True)
            assert navigator.scrapling_service is mock_service

    def test_search(self):
        mock_service = create_mock_scrapling_service()
        with pytest.MonkeyPatch.context() as m:
            m.setattr("scrapper.navigator.indeedScraplingNavigator.ScraplingService", lambda proxies, debug: mock_service)
            navigator = IndeedScraplingNavigator(proxies=[])
            navigator.search("Python", "Barcelona", True, 3, 1)
            mock_service.fetch_with_retry.assert_called()
            url = mock_service.fetch_with_retry.call_args[0][0]
            assert "q=Python" in url
            assert "l=Barcelona" in url
            assert "fromage=3" in url

    def test_get_total_results(self):
        mock_service = create_mock_scrapling_service()
        with pytest.MonkeyPatch.context() as m:
            m.setattr("scrapper.navigator.indeedScraplingNavigator.ScraplingService", lambda proxies, debug: mock_service)
            navigator = IndeedScraplingNavigator(proxies=[])
            mock_selector = MagicMock()
            mock_selector.css = MagicMock(return_value=MockSelector(text="534 empleos"))
            navigator.current_page = mock_selector

            assert navigator.get_total_results("Python") == 534

    def test_get_page_job_links(self):
        mock_service = create_mock_scrapling_service()
        with pytest.MonkeyPatch.context() as m:
            m.setattr("scrapper.navigator.indeedScraplingNavigator.ScraplingService", lambda proxies, debug: mock_service)
            navigator = IndeedScraplingNavigator(proxies=[])

            mock_link1 = MagicMock()
            mock_link1.attrib = {"href": "/test-job-1"}

            mock_link2 = MagicMock()
            mock_link2.attrib = {"href": "/test-job-2"}

            mock_li1 = MagicMock()
            mock_li1.css = MagicMock(return_value=[mock_link1])

            mock_li2 = MagicMock()
            mock_li2.css = MagicMock(return_value=[mock_link2])

            mock_selector = MagicMock()
            mock_selector.css = MagicMock(return_value=[mock_li1, mock_li2])
            navigator.current_page = mock_selector

            links = navigator.get_page_job_links()
            assert links == ["https://es.indeed.com/test-job-1", "https://es.indeed.com/test-job-2"]

    def test_get_job_data(self):
        mock_service = create_mock_scrapling_service()
        with pytest.MonkeyPatch.context() as m:
            m.setattr("scrapper.navigator.indeedScraplingNavigator.ScraplingService", lambda proxies, debug: mock_service)
            navigator = IndeedScraplingNavigator(proxies=[])

            def create_mock_selector(text):
                mock_sel = MockSelector(text=text)
                mock_sel.css = MagicMock(return_value=MockSelector(text=text))
                return mock_sel

            mock_selector = MagicMock()
            mock_selector.url = "https://example.com/job"
            mock_selector.css = MagicMock(side_effect=lambda sel: create_mock_selector(
                "Python Dev" if "title" in sel and "company" not in sel else
                "TechCorp" if "company" in sel and "Location" not in sel else
                "Remote" if "Location" in sel or "location" in sel else
                "60k - 70k" if "Salario" in sel else
                "<b>Description</b>" if "description" in sel.lower() else ""
            ))
            navigator.current_page = mock_selector

            title, company, location, salary, url, html = navigator.get_job_data()
            assert title == "Python Dev"
            assert company == "TechCorp"
            assert location == "Remote"
            assert salary == "60k - 70k"
            assert url == "https://example.com/job"
            assert html == "<b>Description</b>"

    def test_get_job_data_without_salary(self):
        mock_service = create_mock_scrapling_service()
        with pytest.MonkeyPatch.context() as m:
            m.setattr("scrapper.navigator.indeedScraplingNavigator.ScraplingService", lambda proxies, debug: mock_service)
            navigator = IndeedScraplingNavigator(proxies=[])

            def create_mock_selector(text):
                mock_sel = MockSelector(text=text)
                mock_sel.css = MagicMock(return_value=MockSelector(text=text))
                return mock_sel

            mock_selector = MagicMock()
            mock_selector.url = "https://example.com/job"
            mock_selector.css = MagicMock(side_effect=lambda sel: create_mock_selector(
                "Python Dev" if "title" in sel and "company" not in sel else
                "TechCorp" if "company" in sel and "Location" not in sel else
                "Remote" if "Location" in sel or "location" in sel else
                "<b>Description</b>" if "description" in sel.lower() else ""
            ))
            navigator.current_page = mock_selector

            title, company, location, salary, url, html = navigator.get_job_data()
            assert salary == ""

    def test_get_job_data_new_detail_dom(self):
        navigator = _make_navigator()
        navigator.current_page = _new_dom_page()
        assert navigator.get_job_data() == ("Title", "Company", "Madrid, Madrid provincia", "", "https://es.indeed.com/viewjob?jk=abc", "<p>Description</p>")

    @pytest.mark.parametrize("easy,expected", [(True, True), (False, False)])
    def test_check_easy_apply(self, easy, expected):
        navigator = _make_navigator()
        navigator.current_page = _new_dom_page(easy=easy)
        assert navigator.check_easy_apply() is expected

    def test_get_job_data_without_location(self):
        navigator = _make_navigator()
        navigator.current_page = _new_dom_page(location="")
        assert navigator.get_job_data()[2] == ""

    def test_get_total_results_from_title_fallback(self):
        navigator = _make_navigator()
        navigator.current_page = _new_dom_page()
        assert navigator.get_total_results("java") == 25

    @pytest.mark.parametrize("status,expected", [(404, True), (200, False), (None, False)])
    def test_is_delisted_by_status(self, status, expected):
        navigator = _make_navigator()
        navigator.current_page = _new_dom_page()
        navigator.current_page.status = status
        assert navigator.is_delisted() is expected

    def test_is_delisted_by_title(self):
        navigator = _make_navigator()
        page = _new_dom_page()
        page.css = MagicMock(side_effect=lambda sel: MagicMock(get=MagicMock(return_value="No podemos encontrar esta página")) if "h1" in sel else MockSelector(""))
        navigator.current_page = page
        assert navigator.is_delisted() is True

    def test_is_delisted_false_on_valid_page(self):
        navigator = _make_navigator()
        navigator.current_page = _new_dom_page()
        assert navigator.is_delisted() is False