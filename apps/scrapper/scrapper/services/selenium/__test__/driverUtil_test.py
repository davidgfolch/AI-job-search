import pytest

class TestDriverUtil:
    def test_module_imports(self):
        from scrapper.services.selenium import driverUtil
        assert hasattr(driverUtil, 'getDriver')
