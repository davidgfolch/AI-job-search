import pytest
from unittest.mock import MagicMock, patch
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from scrapper.services.selenium import element_service as element_service_module
from scrapper.services.selenium.element_service import ElementService, SCROLL_INTO_VIEW_SCRIPT, SCROLL_CONTAINER_TO_BOTTOM_SCRIPT

ARIA_CHECKBOX_SEL = 'div[role=checkbox][aria-checked="true"]'
NATIVE_CHECKBOX_SEL = 'input[type=checkbox]'
SEL = 'input#query'


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

class TestElementLookup:
    def test_get_elm_resolves_a_css_selector(self, service, driver):
        driver.find_element.return_value = 'elm'
        assert service.getElm(SEL) == 'elm'
        driver.find_element.assert_called_once_with(By.CSS_SELECTOR, SEL)

    def test_get_elm_passes_a_web_element_through(self, service, driver, make_element):
        elm = make_element()
        assert service.getElm(elm) is elm
        driver.find_element.assert_not_called()

    def test_get_elm_of_searches_inside_the_parent(self, service, make_element):
        parent = make_element()
        parent.find_element.return_value = 'child'
        assert service.getElmOf(parent, SEL) == 'child'
        parent.find_element.assert_called_once_with(By.CSS_SELECTOR, SEL)

    def test_get_elms_uses_the_default_driver(self, service, driver):
        driver.find_elements.return_value = ['a', 'b']
        assert service.getElms(SEL) == ['a', 'b']
        driver.find_elements.assert_called_once_with(By.CSS_SELECTOR, SEL)

    def test_get_elms_honours_a_driver_override(self, service, driver):
        override = MagicMock()
        override.find_elements.return_value = ['x']
        assert service.getElms(SEL, override) == ['x']
        driver.find_elements.assert_not_called()

class TestSendKeys:
    def test_aborts_when_the_input_cannot_be_cleared(self, service, driver):
        with patch.object(service, 'waitAndClick'), patch.object(service, 'moveToElement'), \
             patch.object(service, 'clearInputbox', return_value=False):
            assert service.sendKeys(SEL, 'text') is False
        driver.find_element.return_value.send_keys.assert_not_called()

    @pytest.mark.parametrize("text, value", [('text', None), ('', 'typed')], ids=["text", "value_attr"])
    def test_sends_the_whole_value_when_no_pacing_is_given(self, service, driver, make_element, text, value):
        elm = make_element(text=text, value=value)
        driver.find_element.return_value = elm
        with patch.object(service, 'waitAndClick'), patch.object(service, 'moveToElement'), \
             patch.object(service, 'clearInputbox', return_value=True):
            assert service.sendKeys(SEL, value or text) is True
        elm.send_keys.assert_called_once_with(value or text)

    @pytest.mark.parametrize("pacing, expected", [((0.1,), (0.1, 0.1)), ((0.1, 0.2), (0.1, 0.2))], ids=["fixed", "ranged"])
    def test_sends_key_by_key_with_the_requested_pacing(self, service, driver, make_element, no_sleep, pacing, expected):
        elm = make_element(text='ab')
        driver.find_element.return_value = elm
        with patch.object(service, 'waitAndClick'), patch.object(service, 'moveToElement'), \
             patch.object(service, 'clearInputbox', return_value=True):
            service.sendKeys(SEL, 'ab', keyByKeyTime=pacing)
        assert [call.args[0] for call in elm.send_keys.call_args_list] == ['a', 'b']
        assert (expected[0], expected[1]) in [call.args for call in no_sleep.call_args_list]

    def test_can_skip_clearing_the_input(self, service, driver, make_element):
        driver.find_element.return_value = make_element(text='x')
        with patch.object(service, 'waitAndClick'), patch.object(service, 'moveToElement'), \
             patch.object(service, 'clearInputbox') as mock_clear:
            service.sendKeys(SEL, 'x', clear=False)
        mock_clear.assert_not_called()

class TestClearInputbox:
    @pytest.mark.parametrize("mac, select_key", [(True, Keys.COMMAND), (False, Keys.CONTROL)], ids=["mac", "other"])
    def test_selects_all_and_deletes_the_existing_text(self, service, driver, make_element, mac, select_key):
        elm = make_element()
        elm.get_attribute.side_effect = ['old', '']
        driver.find_element.return_value = elm
        with patch.object(element_service_module, 'isMacOS', return_value=mac):
            assert service.clearInputbox(SEL) is True
        assert [call.args[0] for call in elm.send_keys.call_args_list] == [select_key + 'a', Keys.BACKSPACE]

    def test_returns_true_when_the_input_is_already_empty(self, service, driver, make_element):
        elm = make_element(text='', value='')
        elm.get_attribute.return_value = ''
        driver.find_element.return_value = elm
        assert service.clearInputbox(SEL) is True
        elm.send_keys.assert_not_called()

class TestScrollAndClick:
    @pytest.mark.parametrize("block", ['end', 'center'])
    def test_scroll_into_view_runs_the_script_then_waits_and_moves(self, service, driver, make_element, action_chains, block):
        elm = make_element()
        driver.find_element.return_value = elm
        with patch.object(service, 'waitUntilVisible') as mock_visible:
            service.scrollIntoView(SEL, block=block)
        driver.execute_script.assert_called_once_with(SCROLL_INTO_VIEW_SCRIPT.format(block=block), elm)
        mock_visible.assert_called_once_with(elm)
        assert action_chains.call_count == 1

    def test_scroll_container_to_bottom_runs_the_walk_on_the_resolved_element(self, service, driver, make_element):
        elm = make_element()
        driver.find_element.return_value = elm
        service.scrollContainerToBottom(SEL)
        driver.execute_script.assert_called_once_with(SCROLL_CONTAINER_TO_BOTTOM_SCRIPT, elm)

    @pytest.mark.parametrize("failure, expected", [(None, True), (RuntimeError('gone'), False)], ids=["ok", "fails"])
    def test_scroll_into_view_no_error_reports_the_outcome(self, service, failure, expected):
        with patch.object(service, 'scrollIntoView', side_effect=failure):
            assert service.scrollIntoView_noError(SEL) is expected

    def test_wait_and_click_clicks_the_resolved_element(self, service, driver, make_element, action_chains):
        elm = make_element()
        driver.find_element.return_value = elm
        with patch.object(service, 'waitUntilClickable') as mock_clickable:
            service.waitAndClick(SEL, timeout=3)
        mock_clickable.assert_called_once_with(SEL, 3)
        elm.click.assert_called_once()

    def test_wait_and_click_can_scroll_first(self, service, driver, make_element):
        driver.find_element.return_value = make_element()
        with patch.object(service, 'waitUntilClickable'), patch.object(service, 'scrollIntoView') as mock_scroll:
            service.waitAndClick(SEL, scrollIntoView=True)
        mock_scroll.assert_called_once_with(SEL)

    def test_wait_and_click_no_error_delegates_to_try_or_warn(self, service):
        with patch.object(service, 'waitAndClick'):
            assert service.waitAndClick_noError(SEL, 'missing button') is True

class TestWaits:
    @pytest.mark.parametrize("method, condition", [('waitUntilClickable', 'element_to_be_clickable'), ('waitUntilVisible', 'visibility_of'), ('waitUntil_presenceLocatedElement', 'presence_of_element_located')], ids=["clickable", "visible", "presence"])
    def test_builds_a_locator_for_a_css_selector(self, service, driver, wait_mock, method, condition):
        with patch.object(element_service_module, 'EC') as mock_ec:
            getattr(service, method)(SEL, timeout=7)
        wait_mock.assert_called_once_with(driver, 7)
        getattr(mock_ec, condition).assert_called_once_with((By.CSS_SELECTOR, SEL))
        wait_mock.return_value.until.assert_called_once_with(getattr(mock_ec, condition).return_value)

    def test_builds_a_locator_for_a_web_element(self, service, wait_mock, make_element):
        elm = make_element()
        with patch.object(element_service_module, 'EC') as mock_ec:
            service.waitUntilVisible(elm)
        mock_ec.visibility_of.assert_called_once_with(elm)

class TestAttributes:
    def test_get_text_reads_the_element_text(self, service, driver, make_element):
        driver.find_element.return_value = make_element(text='hello')
        assert service.getText(SEL) == 'hello'

    def test_get_attr_returns_a_present_attribute(self, service, driver, make_element):
        driver.find_element.return_value = make_element(value='<b>hi</b>')
        assert service.getAttr(SEL, 'innerHTML') == '<b>hi</b>'

    @pytest.mark.parametrize("method, attr", [('getAttr', 'data-id'), ('getHtml', 'innerHTML')], ids=["attr", "html"])
    def test_reads_raise_for_a_missing_attribute(self, service, driver, make_element, method, attr):
        driver.find_element.return_value = make_element(value='')
        with pytest.raises(Exception, match=f'Could not get attribute {attr}'):
            getattr(service, method)(SEL) if method == 'getHtml' else service.getAttr(SEL, attr)

    def test_get_html_returns_the_inner_html(self, service, driver, make_element):
        driver.find_element.return_value = make_element(value='<p>body</p>')
        assert service.getHtml(SEL) == '<p>body</p>'

    def test_get_attr_of_reads_from_a_nested_element(self, service, make_element):
        parent = make_element()
        parent.find_element.return_value = make_element(value='nested')
        assert service.getAttrOf(parent, SEL, 'data-x') == 'nested'

    def test_set_attr_runs_a_setattribute_script(self, service, driver, make_element):
        elm = make_element()
        assert service.setAttr(elm, 'data-state', 'open') is None
        driver.execute_script.assert_called_once_with("arguments[0].setAttribute('data-state', 'open')", elm)

    def test_move_to_element_accepts_a_css_selector(self, service, driver, make_element, action_chains):
        elm = make_element()
        driver.find_element.return_value = elm
        service.moveToElement(SEL)
        action_chains.return_value.move_to_element.assert_called_once_with(elm)
        action_chains.return_value.move_to_element.return_value.perform.assert_called_once()
