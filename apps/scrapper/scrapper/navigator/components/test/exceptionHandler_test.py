import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.components.exceptionHandler import (
    wait_for_cloudflare_filter, check_for_otp_error, raise_if_otp_invalid,
    wait_for_element_present, is_element_present
)


class TestExceptionHandler:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    def test_wait_for_cloudflare_filter_success(self, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = True
        result = wait_for_cloudflare_filter(mock_selenium, 'input.email')
        assert result is None

    def test_check_for_otp_error_found(self, mock_selenium):
        error_elm = MagicMock()
        error_elm.is_displayed.return_value = True
        mock_selenium.getElms.return_value = [error_elm]
        assert check_for_otp_error(mock_selenium) is True

    def test_check_for_otp_error_not_found(self, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert check_for_otp_error(mock_selenium) is False

    def test_raise_if_otp_invalid_raises(self, mock_selenium):
        error_elm = MagicMock()
        error_elm.is_displayed.return_value = True
        mock_selenium.getElms.return_value = [error_elm]
        with pytest.raises(ValueError, match="Invalid code"):
            raise_if_otp_invalid(mock_selenium, error_message="Invalid code")

    def test_raise_if_otp_invalid_no_error(self, mock_selenium):
        mock_selenium.getElms.return_value = []
        raise_if_otp_invalid(mock_selenium)

    def test_wait_for_element_present_success(self, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = True
        assert wait_for_element_present(mock_selenium, 'button') is True

    def test_is_element_present_true(self, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = True
        assert is_element_present(mock_selenium, 'button') is True

    def test_is_element_present_false(self, mock_selenium):
        mock_selenium.waitUntil_presenceLocatedElement_noError.return_value = False
        assert is_element_present(mock_selenium, 'button') is False
