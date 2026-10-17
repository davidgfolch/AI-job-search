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

    def __bool__(self):
        return bool(self._text)


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


def _make_navigator():
    mock_service = create_mock_scrapling_service()
    with pytest.MonkeyPatch.context() as m:
        m.setattr("scrapper.navigator.indeedScraplingNavigator.ScraplingService", lambda proxies, debug: mock_service)
        return IndeedScraplingNavigator(proxies=[])


def _new_dom_page(easy=True, location="Madrid, Madrid provincia"):
    def css(sel):
        if 'company-info-metadata"] div[dir="ltr"]' in sel:
            return [MagicMock(get_all_text=MagicMock(return_value=location), css=MagicMock(return_value=[]))]
        values = {"vj-job-title": "Title", "vj-company-name": "Company", 'a[href*="/cmp/"]': "Company", "simple-job-description-html": "<p>Description</p>",
                  "viewjob-indeed-apply": "Easy apply" if easy else "", "title::text": "25 empleos de Ingeniero java | Indeed"}
        for key, value in values.items():
            if key in sel:
                return MockSelector(value)
        return MockSelector("")
    page = MagicMock()
    page.url = "https://es.indeed.com/viewjob?jk=abc"
    page.css = MagicMock(side_effect=css)
    return page
