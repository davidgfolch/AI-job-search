import pytest
from unittest.mock import patch, MagicMock
from scrapper.services.selenium.seleniumService import SeleniumService

@pytest.fixture(scope='class')
def mock_driver():
    """Shared mock driver for all tests in the class"""
    driver = MagicMock()
    driver.current_window_handle = 'main_tab'
    driver.window_handles = ['main_tab']
    return driver

@pytest.fixture(scope='class')
def selenium_util(mock_driver):
    """Shared SeleniumService instance with mocked driver"""
    with patch('scrapper.services.selenium.driverUtil.getEnvBool', return_value=False), \
         patch('scrapper.services.selenium.driverUtil.webdriver.Chrome', return_value=mock_driver):
        util = SeleniumService(False)
        yield util
