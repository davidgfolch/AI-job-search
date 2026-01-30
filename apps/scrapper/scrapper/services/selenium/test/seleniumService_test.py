import pytest
from unittest.mock import MagicMock

class TestSeleniumService:
    def test_module_imports(self):
        from scrapper.services.selenium import seleniumService
        assert hasattr(seleniumService, 'SeleniumService')
