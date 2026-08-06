import pytest
from unittest.mock import MagicMock

class TestSeleniumService:
    def test_module_imports(self):
        from scrapper.services.selenium import seleniumService
        assert hasattr(seleniumService, 'SeleniumService')

    def test_set_window_size(self):
        from scrapper.services.selenium.seleniumService import SeleniumService
        mock_browser = MagicMock()
        mock_selenium = MagicMock()
        service = SeleniumService.__new__(SeleniumService)
        service.browser_service = mock_browser
        service.selenium = mock_selenium

        service.set_window_size(500, 600)
        mock_browser.set_window_size.assert_called_once_with(500, 600)

    def test_switch_to_window(self):
        from scrapper.services.selenium.seleniumService import SeleniumService
        mock_browser = MagicMock()
        service = SeleniumService.__new__(SeleniumService)
        service.browser_service = mock_browser

        service.switch_to_window("handle1")
        mock_browser.switch_to_window.assert_called_once_with("handle1")
