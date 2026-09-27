import pytest
from unittest.mock import MagicMock, patch
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from scrapper.services.selenium.element_service import ElementService

ARIA_CHECKBOX_SEL = 'div[role=checkbox][aria-checked="true"]'
NATIVE_CHECKBOX_SEL = 'input[type=checkbox]'


def _aria_checkbox(aria_checked) -> MagicMock:
    elm = MagicMock(spec=WebElement)
    elm.get_attribute.side_effect = lambda attr: {'role': 'checkbox', 'aria-checked': aria_checked}.get(attr)
    return elm


def _native_checkbox(is_selected: bool) -> MagicMock:
    elm = MagicMock(spec=WebElement)
    elm.get_attribute.return_value = None
    elm.is_selected.return_value = is_selected
    return elm


class TestElementService:
    def test_module_imports(self):
        from scrapper.services.selenium import element_service
        assert hasattr(element_service, 'ElementService')

class TestCheckboxUnselect:
    """Aria checkboxes hold their state in aria-checked and only react to a real click, native checkboxes need a js click."""

    @pytest.mark.parametrize("aria_checked, expect_click", [('true', 1), ('false', 0), (None, 0), ('mixed', 0)])
    def test_aria_checkbox(self, aria_checked, expect_click):
        driver, elm = MagicMock(), _aria_checkbox(aria_checked)
        driver.find_element.return_value = elm
        service = ElementService(driver)
        with patch.object(service, 'moveToElement') as mock_move:
            service.checkboxUnselect(ARIA_CHECKBOX_SEL)
        driver.find_element.assert_called_once_with(By.CSS_SELECTOR, ARIA_CHECKBOX_SEL)
        assert elm.click.call_count == expect_click
        assert driver.execute_script.call_count == 0
        assert mock_move.call_count == expect_click

    @pytest.mark.parametrize("is_selected, expect_click", [(True, 1), (False, 0)])
    def test_native_checkbox(self, is_selected, expect_click):
        driver, elm = MagicMock(), _native_checkbox(is_selected)
        driver.find_element.return_value = elm
        service = ElementService(driver)
        with patch.object(service, 'moveToElement') as mock_move:
            service.checkboxUnselect(NATIVE_CHECKBOX_SEL)
        driver.find_element.assert_called_once_with(By.CSS_SELECTOR, NATIVE_CHECKBOX_SEL)
        assert driver.execute_script.call_count == expect_click
        assert elm.click.call_count == 0
        assert mock_move.call_count == expect_click

    def test_accepts_web_element_without_lookup(self):
        driver, elm = MagicMock(), _aria_checkbox('true')
        service = ElementService(driver)
        with patch.object(service, 'moveToElement'):
            service.checkboxUnselect(elm)
        driver.find_element.assert_not_called()
        elm.click.assert_called_once()
