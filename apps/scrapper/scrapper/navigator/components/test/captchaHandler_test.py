import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.components.captchaHandler import _detect_captcha, CSS_SEL_CAPTCHA_CHALLENGE


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
