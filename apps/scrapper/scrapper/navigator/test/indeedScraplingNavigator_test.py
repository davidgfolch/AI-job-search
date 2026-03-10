import pytest
from unittest.mock import MagicMock
from scrapper.navigator.indeedScraplingNavigator import IndeedScraplingNavigator


class MockSelector:
    def __init__(self, text="", html=""):
        self._text = text
        self._html = html
    
    def get(self, default=None):
        return self._text or default
    
    def css(self, selector):
        return MockSelector(self._text)


def create_mock_scrapling_service():
    mock_service = MagicMock()
    mock_service._run_in_thread = MagicMock(side_effect=lambda fn, *args, **kwargs: fn(*args, **kwargs))
    mock_service._init_session = MagicMock()
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.url = "https://es.indeed.com/jobs?q=Python&l=Barcelona"
    
    mock_service.fetch.return_value = mock_response
    mock_service.fetch_with_retry.return_value = mock_response
    mock_service.session = mock_response
    
    return mock_service


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
                "<b>Description</b>" if "Description" in sel else ""
            ))
            navigator.current_page = mock_selector
            
            title, company, location, url, html = navigator.get_job_data()
            assert title == "Python Dev"
            assert company == "TechCorp"
            assert location == "Remote"
            assert url == "https://example.com/job"
            assert html == "<b>Description</b>"
