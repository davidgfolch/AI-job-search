import pytest
from unittest.mock import MagicMock, patch

from scrapper.services.selenium import driverUtil
from scrapper.services.selenium.driverUtil import DriverUtil
from scrapper.test.log_capture import captured_records

LOG_MODULE = "scrapper.driverUtil"


@pytest.fixture
def webdriver_mocks():
    with patch.object(driverUtil.webdriver, "Chrome") as chrome, patch.object(driverUtil.webdriver, "Firefox") as firefox, \
         patch.object(driverUtil, "uc") as uc:
        chrome.return_value = MagicMock()
        firefox.return_value = MagicMock()
        yield {"chrome": chrome, "firefox": firefox, "uc": uc}


def _events(records, event):
    return [r for r in records if r["event"] == event]


class TestModuleSurface:
    def test_module_imports(self):
        assert hasattr(driverUtil, 'DriverUtil')


class TestDriverLogging:
    @pytest.mark.parametrize("browser, attribute", [("chrome", "chrome"), ("firefox", "firefox")], ids=["chrome", "firefox"])
    def test_logs_starting_and_ready(self, webdriver_mocks, browser, attribute):
        with patch.object(driverUtil, "getEnvBool", return_value=False):
            with captured_records(driverUtil, LOG_MODULE) as records:
                sut = DriverUtil(browser)
        webdriver_mocks[attribute].assert_called_once()
        assert _events(records, "driver.starting")[0]["log_level"] == "info"
        assert _events(records, "driver.starting")[0]["browser"] == browser
        assert _events(records, "driver.ready")[0]["log_level"] == "info"
        assert _events(records, "driver.ready")[0]["browser"] == browser
        assert _events(records, "driver.ready")[0]["driver_type"] == "MagicMock"
        assert sut.driver is not None

    def test_logs_undetected_configured(self, webdriver_mocks):
        with patch.object(driverUtil, "getEnvBool", return_value=False):
            with captured_records(driverUtil, LOG_MODULE) as records:
                DriverUtil("chrome")
        configured = _events(records, "driver.undetected_configured")
        assert len(configured) == 1
        assert configured[0]["log_level"] == "info"
        assert configured[0]["undetected"] is False
        assert configured[0]["console"] == "seleniumUtil init (undetected=False)"

    def test_logs_undetected_unavailable(self, webdriver_mocks):
        with patch.object(driverUtil, "getEnvBool", return_value=True):
            with patch.object(DriverUtil, "_findChrome", return_value=None):
                with captured_records(driverUtil, LOG_MODULE) as records:
                    sut = DriverUtil("chrome")
        unavailable = _events(records, "driver.undetected_unavailable")
        assert len(unavailable) == 1
        assert unavailable[0]["log_level"] == "warning"
        assert unavailable[0]["fallback"] == "selenium"
        assert sut.useUndetected is False
        webdriver_mocks["chrome"].assert_called_once()

    @pytest.mark.parametrize("windows, expected_call", [(True, True), (False, True)], ids=["windows", "posix"])
    def test_logs_chrome_version_detected(self, webdriver_mocks, windows, expected_call):
        with patch.object(driverUtil, "getEnvBool", return_value=True):
            with patch.object(DriverUtil, "_findChrome", return_value="chrome.exe"):
                with patch.object(DriverUtil, "_getChromeVersion", return_value=120):
                    with patch.object(driverUtil, "isWindowsOS", return_value=windows):
                        with captured_records(driverUtil, LOG_MODULE) as records:
                            DriverUtil("chrome")
        detected = _events(records, "driver.chrome_version_detected")
        assert len(detected) == 1
        assert detected[0]["log_level"] == "info"
        assert detected[0]["major_version"] == 120
        assert webdriver_mocks["uc"].Chrome.called is expected_call
        assert webdriver_mocks["chrome"].called is False

    def test_logs_chrome_version_detection_failure(self):
        sut = DriverUtil.__new__(DriverUtil)
        with patch.object(driverUtil.subprocess, "run", side_effect=OSError("boom")):
            with patch.object(driverUtil, "isWindowsOS", return_value=True):
                with captured_records(driverUtil, LOG_MODULE) as records:
                    assert sut._getChromeVersion("chrome.exe") == 0
        failed = _events(records, "driver.chrome_version_detection_failed")
        assert len(failed) == 1
        assert failed[0]["log_level"] == "warning"
        assert "boom" in failed[0]["error"]
