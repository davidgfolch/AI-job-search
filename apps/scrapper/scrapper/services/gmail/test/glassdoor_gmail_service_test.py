import pytest
from unittest.mock import MagicMock, patch
from scrapper.services.gmail.email_exceptions import GmailConnectionError


class TestGlassdoorGmailService:
    def test_module_imports(self):
        from scrapper.services.gmail import glassdoor_gmail_service
        assert hasattr(glassdoor_gmail_service, 'GlassdoorGmailService')

    def test_wait_for_glassdoor_verification_code(self):
        from scrapper.services.gmail.glassdoor_gmail_service import GlassdoorGmailService
        service = GlassdoorGmailService(email="test@gmail.com", app_password="pass")
        with patch.object(service, 'wait_for_verification_code', return_value="123456") as mock_wait:
            result = service.wait_for_glassdoor_verification_code(timeout=60)
            assert result == "123456"
            mock_wait.assert_called_with("login@indeed.com", 60)

    def test_sender_is_correct(self):
        from scrapper.services.gmail.glassdoor_gmail_service import GlassdoorGmailService
        assert GlassdoorGmailService.GLASSDOOR_SENDER == "login@indeed.com"

    def test_inherits_from_gmail_service(self):
        from scrapper.services.gmail.glassdoor_gmail_service import GlassdoorGmailService
        from scrapper.services.gmail.generic_gmail_service import GmailService
        assert issubclass(GlassdoorGmailService, GmailService)
