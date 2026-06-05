import pytest
from unittest.mock import MagicMock, patch
from scrapper.services.gmail.email_exceptions import GmailConnectionError


class TestIndeedGmailService:
    def test_module_imports(self):
        from scrapper.services.gmail import indeed_gmail_service
        assert hasattr(indeed_gmail_service, 'IndeedGmailService')

    def test_wait_for_indeed_verification_code(self):
        from scrapper.services.gmail.indeed_gmail_service import IndeedGmailService
        service = IndeedGmailService(email="test@gmail.com", app_password="pass")
        with patch.object(service, 'wait_for_verification_code', return_value="123456") as mock_wait:
            result = service.wait_for_indeed_verification_code(timeout=60)
            assert result == "123456"
            mock_wait.assert_called_with("noreply@indeed.com", 60)

    def test_get_verification_code_from_latest_email(self):
        from scrapper.services.gmail.indeed_gmail_service import IndeedGmailService
        service = IndeedGmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = True
        service.email_reader = MagicMock()
        service.email_reader.get_latest_verification_code.return_value = "654321"
        result = service.get_indeed_verification_code_from_latest_email(timeout=120)
        assert result == "654321"
        service.email_reader.get_latest_verification_code.assert_called_with("noreply@indeed.com", 120)

    def test_get_verification_code_connects_if_not_connected(self):
        from scrapper.services.gmail.indeed_gmail_service import IndeedGmailService
        service = IndeedGmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = False
        with patch.object(service, 'connect', return_value=True) as mock_connect:
            service.email_reader = MagicMock()
            service.email_reader.get_latest_verification_code.return_value = "111111"
            result = service.get_indeed_verification_code_from_latest_email()
            assert result == "111111"
            mock_connect.assert_called_once()

    def test_get_verification_code_raises_on_connect_failure(self):
        from scrapper.services.gmail.indeed_gmail_service import IndeedGmailService
        service = IndeedGmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = False
        with patch.object(service, 'connect', return_value=False):
            with pytest.raises(GmailConnectionError):
                service.get_indeed_verification_code_from_latest_email()

    def test_get_verification_code_re_raises_gmail_error(self):
        from scrapper.services.gmail.indeed_gmail_service import IndeedGmailService
        service = IndeedGmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = True
        service.email_reader = MagicMock()
        service.email_reader.get_latest_verification_code.side_effect = GmailConnectionError("conn err")
        with pytest.raises(GmailConnectionError):
            service.get_indeed_verification_code_from_latest_email()

    def test_get_verification_code_raises_on_other_error(self):
        from scrapper.services.gmail.indeed_gmail_service import IndeedGmailService
        service = IndeedGmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = True
        service.email_reader = MagicMock()
        service.email_reader.get_latest_verification_code.side_effect = Exception("generic error")
        with pytest.raises(GmailConnectionError):
            service.get_indeed_verification_code_from_latest_email()
