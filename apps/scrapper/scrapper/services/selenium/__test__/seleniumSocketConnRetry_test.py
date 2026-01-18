import pytest
from scrapper.services.selenium.seleniumSocketConnRetry import seleniumSocketConnRetry

class TestSeleniumSocketConnRetry:
    def test_decorator_exists(self):
        assert callable(seleniumSocketConnRetry)
    
    def test_decorator_can_be_applied(self):
        @seleniumSocketConnRetry()
        def dummy_function():
            return "test"
        assert dummy_function() == "test"
