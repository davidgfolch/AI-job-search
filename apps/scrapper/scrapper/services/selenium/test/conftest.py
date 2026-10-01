"""Shared fixtures for the selenium service tests.

Kept out of the test modules so each `<source>_test.py` stays focused: the architecture
tests enforce a 1:1 `<source>_test.py` -> `<source>.py` correspondence, which forbids
splitting a suite across several files.
"""
import pytest
from unittest.mock import MagicMock, patch
from selenium.webdriver.remote.webelement import WebElement
from scrapper.services.selenium import element_service as element_service_module
from scrapper.services.selenium.element_service import ElementService

SEL = 'input#query'


@pytest.fixture
def driver():
    return MagicMock()


@pytest.fixture
def service(driver):
    return ElementService(driver)


@pytest.fixture
def make_element():
    """Factory for a WebElement mock that answers text and get_attribute."""
    def build(text: str = '', value=None) -> MagicMock:
        elm = MagicMock(spec=WebElement)
        elm.text = text
        elm.get_attribute.return_value = value
        return elm
    return build


@pytest.fixture(autouse=True)
def no_sleep():
    with patch.object(element_service_module, 'sleep') as mock_sleep:
        yield mock_sleep


@pytest.fixture
def wait_mock():
    with patch.object(element_service_module, 'WebDriverWait') as mock_wait:
        mock_wait.return_value.until = MagicMock()
        yield mock_wait


@pytest.fixture
def action_chains():
    with patch.object(element_service_module.webdriver, 'ActionChains') as mock_chains:
        yield mock_chains
