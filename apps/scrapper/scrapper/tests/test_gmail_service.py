import pytest
from unittest.mock import Mock, patch
from scrapper.services.gmail.generic_gmail_service import GmailService
from scrapper.services.gmail.email_exceptions import (
    GmailConnectionError,
    GmailTimeoutError,
)


class TestGmailService:
    """Test Gmail service functionality"""

    def test_init_with_env_vars(self):
        """Test GmailService initialization with environment variables"""
        with patch(
            "scrapper.services.gmail.generic_gmail_service.getEnv"
        ) as mock_getEnv:
            mock_getEnv.side_effect = lambda key, default=None: {
                "GMAIL_EMAIL": "test@gmail.com",
                "GMAIL_APP_PASSWORD": "test_password",
            }.get(key, default)

            service = GmailService()
            assert service.email == "test@gmail.com"
            assert service.app_password == "test_password"

    def test_init_without_env_vars(self):
        """Test GmailService initialization without environment variables"""
        with patch(
            "scrapper.services.gmail.generic_gmail_service.getEnv"
        ) as mock_getEnv:
            mock_getEnv.return_value = None

            service = GmailService()
            assert service.email is None
            assert service.app_password is None

    def test_extract_verification_code(self):
        """Test verification code extraction from email body"""
        service = GmailService()

        # Mock the email_reader
        service.email_reader = Mock()

        # Test various email formats
        email_bodies = [
            "Your verification code is 123456",
            "Code: 789012",
            "verification code: 456789",
            "Your code: 654321",
        ]

        expected_codes = ["123456", "789012", "456789", "654321"]

        for email_body, expected_code in zip(email_bodies, expected_codes):
            # Configure mock to return expected code for this specific test
            service.email_reader.extract_verification_code_from_subject.return_value = expected_code
            extracted = service.extract_code_from_email(email_body)
            assert extracted == expected_code

    def test_extract_verification_code_no_code(self):
        """Test verification code extraction when no code present"""
        service = GmailService()

        # Mock the email_reader to raise an exception
        service.email_reader = Mock()
        service.email_reader.extract_verification_code_from_subject.side_effect = Exception(
            "No code found"
        )

        with pytest.raises(Exception):  # Should raise VerificationCodeExtractionError
            service.extract_code_from_email("This email has no verification code")

    def test_context_manager(self):
        """Test GmailService as context manager"""
        with patch(
            "scrapper.services.gmail.generic_gmail_service.getEnv"
        ) as mock_getEnv:
            mock_getEnv.side_effect = lambda key, default=None: {
                "GMAIL_EMAIL": "test@gmail.com",
                "GMAIL_APP_PASSWORD": "test_password",
            }.get(key, default)

            with patch.object(GmailService, "connect") as mock_connect:
                with GmailService() as service:
                    assert service.email == "test@gmail.com"
                    assert service.app_password == "test_password"
