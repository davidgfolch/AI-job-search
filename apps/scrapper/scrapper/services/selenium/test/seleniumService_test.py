import pytest
from unittest.mock import MagicMock, patch
from scrapper.services.selenium import seleniumService as seleniumService_module
from scrapper.services.selenium.seleniumService import SeleniumService

BROWSER_DELEGATIONS = [
    ('tabClose', ('tab1',)),
    ('tab', (None,)),
    ('loadPage', ('https://example.com',)),
    ('getUrl', ()),
    ('waitUntilPageUrlContains', ('https://example.com', 5)),
    ('sendEscapeKey', ()),
    ('waitUntilPageIsLoaded', (7,)),
    ('scrollProgressive', (300,)),
    ('back', ()),
    ('wait_for_new_window', (['h1'], 5)),
    ('switch_to_window', ('h2',)),
    ('set_window_size', (500, 600)),
    ('close_and_switch_back', ('h3',)),
]

ELEMENT_DELEGATIONS = [
    ('getElm', ('input#query',)),
    ('getElmOf', ('parent', 'input#query')),
    ('getElms', ('input#query', None)),
    ('sendKeys', ('input#query', 'value', (0.1, 0.2), True)),
    ('clearInputbox', ('input#query',)),
    ('checkboxUnselect', ('input#query',)),
    ('scrollIntoView', ('input#query',)),
    ('waitUntilClickable', ('input#query', 5)),
    ('waitUntilVisible', ('input#query', 5)),
    ('waitUntil_presenceLocatedElement', ('input#query', 5)),
    ('waitAndClick', ('input#query', 5, True)),
    ('waitAndClick_noError', ('input#query', 'missing', True)),
    ('scrollIntoView_noError', ('input#query',)),
    ('moveToElement', ('input#query',)),
    ('getHtml', ('input#query',)),
    ('getText', ('input#query',)),
    ('getAttr', ('input#query', 'data-id')),
    ('getAttrOf', ('parent', 'input#query', 'data-id')),
    ('setAttr', ('input#query', 'data-state', 'open')),
]


@pytest.fixture
def service():
    sut = SeleniumService.__new__(SeleniumService)
    sut.debug = False
    sut.driver = MagicMock()
    sut.driverUtil = MagicMock()
    sut.browser_service = MagicMock()
    sut.element_service = MagicMock()
    return sut


class TestConstruction:
    def test_wires_the_driver_and_the_two_sub_services(self):
        with patch.object(seleniumService_module, 'DriverUtil') as driver_util_cls, \
             patch.object(seleniumService_module, 'BrowserService') as browser_cls, \
             patch.object(seleniumService_module, 'ElementService') as element_cls:
            driver_util_cls.return_value.driver = 'driver'
            sut = SeleniumService(True, 'firefox')
        driver_util_cls.assert_called_once_with('firefox')
        browser_cls.assert_called_once_with('driver')
        element_cls.assert_called_once_with('driver')
        assert sut.driver == 'driver'
        assert sut.debug is True

    def test_exposes_the_undetected_driver_flag(self, service):
        service.driverUtil.useUndetected = True
        assert service.usesUndetectedDriver() is True


class TestContextManager:
    def test_enter_returns_the_service(self, service):
        with service as entered:
            assert entered is service

    def test_exit_closes_the_driver(self, service):
        quit = service.driver.quit
        service.__exit__(None, None, None)
        quit.assert_called_once()

    def test_exit_quits_and_then_neutralises_a_second_quit(self, service):
        service.exit()
        assert service.driver.quit() is None

    def test_exit_swallows_a_failing_quit(self, service):
        service.driver.quit.side_effect = RuntimeError('already gone')
        service.exit()
        assert callable(service.driver.quit)


class TestDelegation:
    @pytest.mark.parametrize("method, args", BROWSER_DELEGATIONS, ids=[name for name, _ in BROWSER_DELEGATIONS])
    def test_delegates_to_the_browser_service(self, service, method, args):
        getattr(service, method)(*args)
        getattr(service.browser_service, method).assert_called_once_with(*args)

    @pytest.mark.parametrize("method, args", ELEMENT_DELEGATIONS, ids=[name for name, _ in ELEMENT_DELEGATIONS])
    def test_delegates_to_the_element_service(self, service, method, args):
        getattr(service, method)(*args)
        getattr(service.element_service, method).assert_called_once_with(*args)

    def test_returns_the_value_from_the_element_service(self, service):
        service.element_service.getText.return_value = 'hello'
        assert service.getText('input#query') == 'hello'

    def test_defaul_tab_reads_the_browser_service(self, service):
        service.browser_service.default_tab = 'default'
        assert service.defaulTab == 'default'

    def test_tabs_reads_the_browser_service(self, service):
        service.browser_service.tabs = ['a', 'b']
        assert service.tabs == ['a', 'b']


class TestSetFocus:
    def test_focuses_the_resolved_element(self, service):
        service.element_service.getElm.return_value = 'elm'
        service.setFocus('input#query')
        service.driver.execute_script.assert_called_once_with('arguments[0].focus();', 'elm')


class TestPresenceWaitNoError:
    def test_returns_true_when_the_element_appears(self, service):
        assert service.waitUntil_presenceLocatedElement_noError('input#query', 5) is True
        service.element_service.waitUntil_presenceLocatedElement.assert_called_once_with('input#query', 5)

    def test_returns_false_when_the_element_never_appears(self, service):
        service.element_service.waitUntil_presenceLocatedElement.side_effect = RuntimeError('timeout')
        assert service.waitUntil_presenceLocatedElement_noError('input#query', 5) is False
