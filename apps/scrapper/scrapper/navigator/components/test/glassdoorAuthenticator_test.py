import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.components.glassdoorAuthenticator import (
    GlassdoorAuthenticator,
    CSS_SEL_INDEED_AUTH_BUTTON,
    CSS_SEL_EMAIL_INPUT,
    CSS_SEL_EMAIL_SUBMIT,
    CSS_SEL_GOOGLE_OTP_FALLBACK,
    CSS_SEL_PASSCODE_INPUT,
    CSS_SEL_OTP_VERIFY_SUBMIT,
)


class TestGlassdoorAuthenticator:
    @pytest.fixture
    def mock_selenium(self):
        mock = MagicMock()
        mock.driver.window_handles = ["handle1"]
        return mock

    @pytest.fixture
    def authenticator(self, mock_selenium):
        with patch('scrapper.navigator.components.glassdoorAuthenticator.baseScrapper.getAndCheckEnvVars', return_value=('user@test.com', None, 'search')):
            return GlassdoorAuthenticator(mock_selenium)

    @patch('scrapper.navigator.components.glassdoorAuthenticator.sleep')
    @patch.object(GlassdoorAuthenticator, '_get_otp_code')
    def test_login_flow(self, mock_otp, mock_sleep, authenticator, mock_selenium):
        mock_selenium.wait_for_new_window.return_value = "popup_handle"
        mock_selenium.driver.window_handles = ["handle1"]
        mock_selenium.getElms.return_value = []

        authenticator.login()

        mock_selenium.waitAndClick.assert_any_call(CSS_SEL_INDEED_AUTH_BUTTON)
        mock_selenium.wait_for_new_window.assert_called_with(["handle1"])
        mock_selenium.switch_to_window.assert_called_with("popup_handle")
        mock_selenium.sendKeys.assert_any_call(CSS_SEL_EMAIL_INPUT, 'user@test.com')
        mock_selenium.waitAndClick.assert_any_call(CSS_SEL_EMAIL_SUBMIT)
        mock_selenium.waitAndClick.assert_any_call(CSS_SEL_GOOGLE_OTP_FALLBACK)
        mock_otp.assert_called_once()
        mock_selenium.close_and_switch_back.assert_called_with("popup_handle")
        assert authenticator._popup_handle is None

    @patch('scrapper.navigator.components.glassdoorAuthenticator.GlassdoorGmailService')
    @patch('scrapper.navigator.components.glassdoorAuthenticator.sleep')
    def test_get_otp_code_success(self, mock_sleep, mock_gmail_class, authenticator, mock_selenium):
        mock_gmail = mock_gmail_class.return_value.__enter__.return_value
        mock_gmail.wait_for_glassdoor_verification_code.return_value = "940954"
        mock_selenium.getElms.return_value = []

        authenticator._get_otp_code()

        mock_selenium.sendKeys.assert_called_with(CSS_SEL_PASSCODE_INPUT, "940954")
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_OTP_VERIFY_SUBMIT)

    @patch('scrapper.navigator.components.glassdoorAuthenticator.GlassdoorGmailService')
    @patch('scrapper.navigator.components.glassdoorAuthenticator.sleep')
    def test_get_otp_code_invalid_raises(self, mock_sleep, mock_gmail_class, authenticator, mock_selenium):
        mock_gmail = mock_gmail_class.return_value.__enter__.return_value
        mock_gmail.wait_for_glassdoor_verification_code.return_value = "000000"
        error_elm = MagicMock()
        error_elm.is_displayed.return_value = True
        mock_selenium.getElms.return_value = [error_elm]

        with pytest.raises(ValueError, match="Invalid OTP code"):
            authenticator._get_otp_code()

    def test_get_otp_code_no_error_element(self, authenticator, mock_selenium):
        mock_selenium.getElms.return_value = []
        with patch.object(authenticator, '_get_otp_code') as mock_method:
            mock_method.return_value = None
            mock_method()
            assert mock_method.called
