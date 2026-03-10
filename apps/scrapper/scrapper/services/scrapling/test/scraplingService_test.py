import pytest
from unittest.mock import MagicMock, patch


class TestScraplingService:
    def test_init_without_proxies(self):
        with patch('scrapper.services.scrapling.scraplingService.StealthySession') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            from scrapper.services.scrapling.scraplingService import ScraplingService
            service = ScraplingService(proxies=None, debug=False)
            mock_session.start.assert_called_once()

    def test_init_with_proxies(self):
        with patch('scrapper.services.scrapling.scraplingService.StealthySession') as mock_session_cls, \
             patch('scrapper.services.scrapling.scraplingService.ProxyRotator') as mock_rotator_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            mock_rotator_cls.return_value = "rotator"
            from scrapper.services.scrapling.scraplingService import ScraplingService
            service = ScraplingService(proxies=["http://proxy1", "http://proxy2"], debug=True)
            mock_session.start.assert_called_once()
            mock_rotator_cls.assert_called_once_with(["http://proxy1", "http://proxy2"])

    def test_close(self):
        with patch('scrapper.services.scrapling.scraplingService.StealthySession') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            from scrapper.services.scrapling.scraplingService import ScraplingService
            service = ScraplingService(proxies=[], debug=False)
            service.close()
            mock_session.close.assert_called_once()

    def test_shutdown(self):
        with patch('scrapper.services.scrapling.scraplingService.StealthySession') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            from scrapper.services.scrapling.scraplingService import ScraplingService
            service = ScraplingService(proxies=[], debug=False)
            service.close()
            mock_session.close.assert_called_once()
