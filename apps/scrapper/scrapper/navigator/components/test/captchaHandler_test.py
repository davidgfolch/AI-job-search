import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.components import captchaHandler
from scrapper.navigator.components.captchaHandler import _detect_captcha, CSS_SEL_CAPTCHA_CHALLENGE
from scrapper.test.log_capture import captured_records

LOG_MODULE = "scrapper.captchaHandler"


class TestCaptchaHandler:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    def test_detect_captcha_found(self, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = True
        result = _detect_captcha(mock_selenium, CSS_SEL_CAPTCHA_CHALLENGE)
        assert result is None
        mock_selenium.waitUntil_presenceLocatedElement_noError.assert_called_once_with(CSS_SEL_CAPTCHA_CHALLENGE)

    def test_detect_captcha_not_found_retries(self, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = False
        with patch('commonlib.decorator.retry.sleep') as mock_sleep:
            result = _detect_captcha(mock_selenium, CSS_SEL_CAPTCHA_CHALLENGE)
        assert result is False
        assert mock_selenium.waitUntil_presenceLocatedElement_noError.call_count == 61
        assert mock_sleep.call_count == 60

    def test_detect_captcha_logs_warning_event(self, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = False
        with patch('commonlib.decorator.retry.sleep'):
            with captured_records(captchaHandler, LOG_MODULE) as records:
                _detect_captcha(mock_selenium, CSS_SEL_CAPTCHA_CHALLENGE)
        captcha_records = [r for r in records if r["event"].startswith("captcha.")]
        assert captcha_records
        assert {r["event"] for r in captcha_records} == {"captcha.detected"}
        assert {r["log_level"] for r in captcha_records} == {"warning"}
        assert {r["selector"] for r in captcha_records} == {CSS_SEL_CAPTCHA_CHALLENGE}

    def test_detect_captcha_found_logs_nothing(self, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = True
        with captured_records(captchaHandler, LOG_MODULE) as records:
            _detect_captcha(mock_selenium, CSS_SEL_CAPTCHA_CHALLENGE)
        assert [r for r in records if r["event"].startswith("captcha.")] == []
