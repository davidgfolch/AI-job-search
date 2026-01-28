import pytest
from unittest.mock import patch, MagicMock
from selenium.webdriver.common.by import By

class TestSeleniumServiceInteraction:
    def test_get_elm_success(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        result = selenium_util.getElm('#test-id')
        assert result == mock_element
        mock_driver.find_element.assert_called_with(By.CSS_SELECTOR, '#test-id')

    def test_get_elms_success(self, selenium_util, mock_driver):
        mock_elements = [MagicMock(), MagicMock()]
        mock_driver.find_elements.return_value = mock_elements
        result = selenium_util.getElms('.test-class')
        assert result == mock_elements
        mock_driver.find_elements.assert_called_with(By.CSS_SELECTOR, '.test-class')

    def test_send_keys(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        with patch.object(selenium_util.element_service, 'moveToElement'):
            selenium_util.sendKeys('#test-id', 'test text')
            mock_element.send_keys.assert_called_with('test text')

    def test_get_text(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_element.text = 'Test text'
        mock_driver.find_element.return_value = mock_element
        result = selenium_util.getText('#test-id')
        assert result == 'Test text'

    def test_get_attr(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = 'test-value'
        mock_driver.find_element.return_value = mock_element
        result = selenium_util.getAttr('#test-id', 'href')
        assert result == 'test-value'
        mock_element.get_attribute.assert_called_with('href')

    def test_scroll_into_view(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        with patch.object(selenium_util.element_service, 'waitUntilVisible'), \
             patch.object(selenium_util.element_service, 'moveToElement'):
            selenium_util.scrollIntoView('#test-id')
            mock_driver.execute_script.assert_called()

    def test_checkbox_unselect(self, selenium_util, mock_driver):
        mock_driver.reset_mock()
        mock_checkbox = MagicMock()
        mock_checkbox.is_selected.return_value = True
        mock_driver.find_element.return_value = mock_checkbox
        with patch.object(selenium_util.element_service, 'moveToElement'):
            selenium_util.checkboxUnselect('#checkbox')
            mock_driver.execute_script.assert_called()

    def test_wait_and_click(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        with patch.object(selenium_util.element_service, 'waitUntilClickable'), \
             patch.object(selenium_util.element_service, 'moveToElement'):
            selenium_util.waitAndClick('#test-id')
            mock_element.click.assert_called()

    @pytest.mark.parametrize("side_effect,expected", [(None, True), (Exception, False)])
    def test_wait_and_click_no_error(self, side_effect, expected, selenium_util):
        with patch.object(selenium_util.element_service, 'waitAndClick', side_effect=side_effect):
            assert selenium_util.waitAndClick_noError('#test-id', 'msg') is expected

    def test_get_html(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = '<div>test</div>'
        mock_driver.find_element.return_value = mock_element
        assert selenium_util.getHtml('#test-id') == '<div>test</div>'

    def test_set_focus(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        selenium_util.setFocus('#test-id')
        mock_driver.execute_script.assert_called_with("arguments[0].focus();", mock_element)

    @pytest.mark.parametrize("side_effect,expected", [(None, True), (Exception, False)])
    def test_wait_until_presence_no_error(self, side_effect, expected, selenium_util):
        with patch.object(selenium_util.element_service, 'waitUntil_presenceLocatedElement', side_effect=side_effect):
            assert selenium_util.waitUntil_presenceLocatedElement_noError('#test-id') is expected

    def test_scroll_into_view_no_error(self, selenium_util):
        with patch.object(selenium_util.element_service, 'scrollIntoView'):
            assert selenium_util.scrollIntoView_noError('#test-id') is True

    def test_move_to_element(self, selenium_util):
        with patch.object(selenium_util.element_service, 'moveToElement') as mock_move:
            selenium_util.moveToElement('#test-id')
            mock_move.assert_called_with('#test-id')

    def test_set_attr(self, selenium_util):
        with patch.object(selenium_util.element_service, 'setAttr') as mock_set:
            selenium_util.setAttr('#test-id', 'attr', 'val')
            mock_set.assert_called_with('#test-id', 'attr', 'val')

    def test_get_attr_of(self, selenium_util):
        mock_element = MagicMock()
        with patch.object(selenium_util.element_service, 'getAttrOf', return_value='val') as mock_get:
            assert selenium_util.getAttrOf(mock_element, '#sub', 'attr') == 'val'
            mock_get.assert_called_with(mock_element, '#sub', 'attr')
