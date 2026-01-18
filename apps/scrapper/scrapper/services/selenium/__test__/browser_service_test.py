import pytest
from unittest.mock import MagicMock
from selenium import webdriver

class TestBrowserService:
    def test_module_imports(self):
        from scrapper.services.selenium import browser_service
        assert hasattr(browser_service, 'BrowserService')
