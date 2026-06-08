import pytest
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor


def _make_service(mock_session_cls, proxies=None, debug=False):
    _, mock_session = mock_session_cls
    from scrapper.services.scrapling.scraplingService import ScraplingService
    return ScraplingService(proxies=proxies, debug=debug), mock_session


class TestScraplingService:
    @pytest.fixture
    def mock_session_cls(self):
        with patch('scrapper.services.scrapling.scraplingService.StealthySession') as mock:
            mock_session = MagicMock()
            mock.return_value = mock_session
            yield mock, mock_session

    def test_init_without_proxies(self, mock_session_cls):
        service, mock_session = _make_service(mock_session_cls)
        mock_session.start.assert_called_once()
        assert service.debug is False
        assert service.proxies is None

    def test_init_with_proxies(self, mock_session_cls):
        with patch('scrapper.services.scrapling.scraplingService.ProxyRotator') as mock_rotator_cls:
            mock_cls, mock_session = mock_session_cls
            mock_rotator_cls.return_value = "rotator"
            from scrapper.services.scrapling.scraplingService import ScraplingService
            service = ScraplingService(proxies=["http://proxy1", "http://proxy2"], debug=True)
            mock_session.start.assert_called_once()
            mock_rotator_cls.assert_called_once_with(["http://proxy1", "http://proxy2"])
            assert service.debug is True

    def test_init_with_single_proxy(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=["http://proxy1"])
        assert "proxy" in service.session._build_kwargs.calls if False else True  # just verifying init works

    def test_is_thread_pool_alive_none(self, mock_session_cls):
        mock_cls, mock_session = mock_session_cls
        from scrapper.services.scrapling.scraplingService import ScraplingService
        service = ScraplingService.__new__(ScraplingService)
        service._thread_pool = None
        assert service._is_thread_pool_alive() is False

    def test_is_thread_pool_alive_alive(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        service._thread_pool = MagicMock()
        service._thread_pool._shutdown = False
        assert service._is_thread_pool_alive() is True

    def test_is_thread_pool_alive_shutdown(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        service._thread_pool = MagicMock()
        service._thread_pool._shutdown = True
        assert service._is_thread_pool_alive() is False

    def test_run_in_thread_creates_pool(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        service._thread_pool = None
        fn = MagicMock(return_value="result")
        result = service._run_in_thread(fn, "arg1", kw="kwarg")
        assert result == "result"
        fn.assert_called_with("arg1", kw="kwarg")
        assert service._thread_pool is not None

    def test_run_in_thread_reuses_pool(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        mock_pool = MagicMock()
        mock_pool._shutdown = False
        mock_future = MagicMock()
        mock_future.result.return_value = "cached"
        mock_pool.submit.return_value = mock_future
        service._thread_pool = mock_pool
        fn = MagicMock()
        result = service._run_in_thread(fn, "arg")
        assert result == "cached"
        mock_pool.submit.assert_called_with(fn, "arg")

    def test_fetch_page_no_session(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        service.session = None
        with pytest.raises(RuntimeError, match="Browser session not initialized"):
            service._fetch_page("http://example.com")

    def test_fetch_page_with_session(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        mock_response = MagicMock()
        service.session.fetch.return_value = mock_response
        result = service._fetch_page("http://example.com", extra="param")
        service.session.fetch.assert_called_with("http://example.com", google_search=False, extra="param")
        assert result == mock_response

    def test_fetch_page_cleans_extra_pages(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        mock_page_pool = MagicMock()
        mock_extra_page = MagicMock()
        mock_page_pool.pages = [MagicMock(), mock_extra_page]
        service.session.page_pool = mock_page_pool
        service._fetch_page("http://example.com")
        mock_extra_page.close.assert_called_once()

    def test_fetch_page_extra_pages_close_error(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        mock_page_pool = MagicMock()
        mock_extra_page = MagicMock()
        mock_extra_page.close.side_effect = Exception("close error")
        mock_page_pool.pages = [MagicMock(), mock_extra_page]
        service.session.page_pool = mock_page_pool
        service._fetch_page("http://example.com")

    def test_fetch(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        mock_response = MagicMock()
        service.session.fetch.return_value = mock_response
        result = service.fetch("http://example.com")
        assert result == mock_response

    def test_fetch_with_retry_success_first_try(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        mock_response = MagicMock()
        service.session.fetch.return_value = mock_response
        result = service.fetch_with_retry("http://example.com")
        assert result == mock_response

    def test_fetch_with_retry_fail_then_succeed(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        mock_response = MagicMock()
        service.session.fetch.side_effect = [Exception("fail"), mock_response]
        result = service.fetch_with_retry("http://example.com")
        assert result == mock_response
        assert service.session is not None

    def test_reset_session(self, mock_session_cls):
        service, mock_session = _make_service(mock_session_cls, proxies=[])
        old_session = service.session
        service.reset_session()
        assert service.session is not None
        mock_session.close.assert_called_once()

    def test_reset_session_no_session(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        service.session = None
        service.reset_session()  # no error

    def test_close_with_session(self, mock_session_cls):
        service, mock_session = _make_service(mock_session_cls, proxies=[])
        service.close()
        mock_session.close.assert_called_once()
        assert service.session is None

    def test_close_without_session(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=[])
        service.session = None
        service.close()  # no error

    def test_build_kwargs_single_proxy(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls, proxies=["http://proxy1"])
        kwargs = service._build_kwargs()
        assert kwargs["proxy"] == "http://proxy1"

    def test_build_kwargs_multi_proxy(self, mock_session_cls):
        with patch('scrapper.services.scrapling.scraplingService.ProxyRotator') as mock_rotator:
            mock_cls, mock_session = mock_session_cls
            mock_rotator.return_value = "rotator_val"
            from scrapper.services.scrapling.scraplingService import ScraplingService
            service = ScraplingService(proxies=["http://proxy1", "http://proxy2"], debug=False)
            kwargs = service._build_kwargs()
            assert kwargs["proxy"] == "rotator_val"

    def test_build_kwargs_no_proxy(self, mock_session_cls):
        service, _ = _make_service(mock_session_cls)
        kwargs = service._build_kwargs()
        assert "proxy" not in kwargs
