import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.components.indeedAuthenticator import (
    IndeedAuthenticator,
    CSS_SEL_COOKIE_ACCEPT,
    CSS_SEL_LOGIN_EMAIL,
    CSS_SEL_LOGIN_SUBMIT,
    LOGIN_PAGE,
    CSS_SEL_2FA_PASSCODE_INPUT,
    CSS_SEL_2FA_VERIFY_SUBMIT,
    CSS_SEL_WEBAUTHN_CONTINUE
)

class TestIndeedAuthenticator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def authenticator(self, mock_selenium):
        with patch('scrapper.navigator.components.indeedAuthenticator.baseScrapper.getAndCheckEnvVars', return_value=('user@test.com', 'pass', 'key')):
            return IndeedAuthenticator(mock_selenium)

    def test_accept_cookies(self, authenticator, mock_selenium):
        authenticator.accept_cookies()
        mock_selenium.waitAndClick_noError.assert_called_with(CSS_SEL_COOKIE_ACCEPT, "Could not accept cookies")

    def test_waitForCloudflareFilterInLogin(self, authenticator, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = True
        assert authenticator.waitForCloudflareFilterInLogin() is True
        mock_selenium.waitUntil_presenceLocatedElement_noError.assert_called()

    @patch('scrapper.navigator.components.indeedAuthenticator.sleep')
    @patch.object(IndeedAuthenticator, 'click_google_otp_fallback')
    @patch.object(IndeedAuthenticator, 'getEmail2faCode')
    @patch.object(IndeedAuthenticator, 'ignore_access_key_form')
    def test_login_success(self, mock_ignore, mock_2fa, mock_otp, mock_sleep, authenticator, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.side_effect = [False, False, False]
        with patch.object(IndeedAuthenticator, 'waitForCloudflareFilterInLogin', return_value=True), \
             patch.object(IndeedAuthenticator, 'accept_cookies') as mock_accept:
            
            authenticator.login()
            
            mock_selenium.loadPage.assert_called_with(LOGIN_PAGE)
            mock_selenium.sendKeys.assert_any_call(CSS_SEL_LOGIN_EMAIL, 'user@test.com')
            mock_accept.assert_called_once()
            mock_selenium.waitAndClick.assert_any_call(CSS_SEL_LOGIN_SUBMIT)
            mock_otp.assert_called_once()
            mock_2fa.assert_called_once()
            mock_ignore.assert_called_once()

    def test_login_already_logged_in(self, authenticator, mock_selenium):
        with patch.object(IndeedAuthenticator, 'waitForCloudflareFilterInLogin', return_value=True):
             mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = True # AccountMenu found
             authenticator.login()
             # Should return early
             mock_selenium.sendKeys.assert_not_called()

    @patch('scrapper.navigator.components.indeedAuthenticator.IndeedGmailService')
    @patch('scrapper.navigator.components.indeedAuthenticator.sleep')
    def test_getEmail2faCode_success(self, mock_sleep, mock_gmail_class, authenticator, mock_selenium):
        mock_gmail = mock_gmail_class.return_value.__enter__.return_value
        mock_gmail.wait_for_verification_code.return_value = "123456"
        mock_selenium.getElms.return_value = []
        
        authenticator.getEmail2faCode()
        
        mock_selenium.sendKeys.assert_called_with(CSS_SEL_2FA_PASSCODE_INPUT, "123456")
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_2FA_VERIFY_SUBMIT)

    def test_ignore_access_key_form(self, authenticator, mock_selenium):
        authenticator.ignore_access_key_form()
        mock_selenium.waitUntil_presenceLocatedElement.assert_called_with(CSS_SEL_WEBAUTHN_CONTINUE)
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_WEBAUTHN_CONTINUE)
