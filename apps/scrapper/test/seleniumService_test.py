import pytest
from unittest.mock import patch, MagicMock
from selenium.webdriver.common.by import By

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
    with patch('scrapper.driverUtil.getEnvBool', return_value=False), \
         patch('scrapper.driverUtil.webdriver.Chrome', return_value=mock_driver):
        util = SeleniumService()
        yield util


class TestSeleniumService:
    def test_initialization(self, selenium_util, mock_driver):
        assert selenium_util.driver == mock_driver

    def test_load_page(self, selenium_util, mock_driver):
        selenium_util.loadPage('https://test.com')
        mock_driver.get.assert_called_with('https://test.com')

    def test_get_url(self, selenium_util, mock_driver):
        mock_driver.current_url = 'https://test.com'
        result = selenium_util.getUrl()
        assert result == 'https://test.com'

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

    def test_tab_creation(self, selenium_util, mock_driver):
        mock_driver.current_window_handle = 'new_tab'
        with patch.object(selenium_util.browser_service, 'waitUntilPageIsLoaded'):
            selenium_util.tab('test_tab')
            assert 'test_tab' in selenium_util.tabs

    def test_tab_close(self, selenium_util, mock_driver):
        selenium_util.tabs['test_tab'] = 'handle'
        selenium_util.tabClose('test_tab')
        mock_driver.close.assert_called()
        assert 'test_tab' not in selenium_util.tabs

    @patch('scrapper.services.selenium.browser_service.WebDriverWait')
    def test_wait_until_page_is_loaded(self, mock_wait, selenium_util, mock_driver):
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        selenium_util.waitUntilPageIsLoaded(10)
        mock_wait.assert_called_with(mock_driver, 10)

    @patch('scrapper.services.selenium.browser_service.sleep')
    def test_scroll_progressive_down(self, mock_sleep, selenium_util, mock_driver):
        mock_driver.execute_script.side_effect = [100] + [None] * 20
        selenium_util.scrollProgressive(200)
        assert mock_driver.execute_script.call_count >= 3
        final_call = mock_driver.execute_script.call_args_list[-1]
        assert 'window.scrollTo(0, 300)' in str(final_call)

    @patch('scrapper.services.selenium.browser_service.sleep')
    def test_scroll_progressive_up(self, mock_sleep, selenium_util, mock_driver):
        mock_driver.execute_script.side_effect = [500] + [None] * 20
        selenium_util.scrollProgressive(-200)
        assert mock_driver.execute_script.call_count >= 3
        final_call = mock_driver.execute_script.call_args_list[-1]
        assert 'window.scrollTo(0, 300)' in str(final_call)

    @patch('scrapper.services.selenium.browser_service.sleep')
    def test_scroll_progressive_zero(self, mock_sleep, selenium_util, mock_driver):
        mock_driver.execute_script.side_effect = [100, None]
        selenium_util.scrollProgressive(0)
        final_call = mock_driver.execute_script.call_args_list[-1]
        assert 'window.scrollTo(0, 100)' in str(final_call)

    def test_send_escape_key(self, selenium_util):
        with patch('scrapper.services.selenium.browser_service.webdriver.ActionChains') as mock_action:
            mock_chain = MagicMock()
            mock_action.return_value = mock_chain
            selenium_util.sendEscapeKey()
            mock_chain.send_keys.assert_called()

    def test_checkbox_unselect(self, selenium_util, mock_driver):
        mock_driver.reset_mock()
        mock_checkbox = MagicMock()
        mock_checkbox.is_selected.return_value = True
        mock_driver.find_element.return_value = mock_checkbox
        mock_driver.execute_script.return_value = None
        mock_driver.execute_script.side_effect = None

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

    def test_wait_and_click_no_error_success(self, selenium_util):
        with patch.object(selenium_util.element_service, 'waitAndClick'):
            result = selenium_util.waitAndClick_noError('#test-id', 'test message')
            assert result is True

    def test_wait_and_click_no_error_failure(self, selenium_util):
        with patch.object(selenium_util.element_service, 'waitAndClick', side_effect=Exception('error')):
            result = selenium_util.waitAndClick_noError('#test-id', 'test message')
            assert result is False

    def test_get_html(self, selenium_util, mock_driver):
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = '<div>test</div>'
        mock_driver.find_element.return_value = mock_element

        result = selenium_util.getHtml('#test-id')
        assert result == '<div>test</div>'

    def test_back(self, selenium_util, mock_driver):
        selenium_util.back()
        mock_driver.back.assert_called_once()

    def test_exit_driver_alive(self, selenium_util, mock_driver):
        selenium_util.exit()
        mock_driver.quit.assert_called()

    def test_tab_close_error_handling(self, selenium_util, mock_driver):
        selenium_util.tabs['test_tab'] = 'handle'
        mock_driver.close.side_effect = Exception('Close error')
        selenium_util.tabClose('test_tab')
        mock_driver.close.side_effect = None
