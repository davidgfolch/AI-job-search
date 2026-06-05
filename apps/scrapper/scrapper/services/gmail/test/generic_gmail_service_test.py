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

    def test_is_connected(self):
        """Test is_connected method"""
        service = GmailService()
        assert service.is_connected() is False
        service._is_connected = True
        assert service.is_connected() is True

    def test_close(self):
        """Test close method"""
        service = GmailService()
        service.email_reader = Mock()
        service.close()
        service.email_reader.close.assert_called_once()
        assert service._is_connected is False

    def test_wait_for_verification_code_not_connected(self):
        """Test wait_for_verification_code when not connected"""
        service = GmailService()
        service._is_connected = False
        with patch.object(service, 'connect', return_value=True):
            service.email_reader = Mock()
            service.email_reader.get_latest_verification_code.return_value = "123456"
            result = service.wait_for_verification_code("test@example.com")
            assert result == "123456"

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

    def test_connect_without_credentials(self):
        """Test connect fails when credentials missing"""
        service = GmailService()
        service.email = None
        service.app_password = None
        result = service.connect()
        assert result is False
        assert service._is_connected is False

    def test_connect_exception(self):
        """Test connect handles exception gracefully"""
        service = GmailService(email="test@gmail.com", app_password="pass")
        with patch('scrapper.services.gmail.generic_gmail_service.EmailReader') as mock_reader:
            mock_reader.side_effect = Exception("Connection failed")
            result = service.connect()
            assert result is False
            assert service._is_connected is False

    def test_connect_success(self):
        """Test connect succeeds"""
        service = GmailService(email="test@gmail.com", app_password="pass")
        with patch('scrapper.services.gmail.generic_gmail_service.EmailReader') as mock_reader:
            mock_reader_instance = Mock()
            mock_reader.return_value = mock_reader_instance
            result = service.connect()
            assert result is True
            assert service._is_connected is True
            mock_reader_instance.connect.assert_called_once()

    def test_wait_for_verification_code_already_connected(self):
        """Test wait for verification code when already connected"""
        service = GmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = True
        service.email_reader = Mock()
        service.email_reader.get_latest_verification_code.return_value = "654321"
        result = service.wait_for_verification_code("sender@example.com", timeout=60)
        assert result == "654321"
        service.email_reader.get_latest_verification_code.assert_called_with("sender@example.com", 60)

    def test_wait_for_verification_code_connect_fails(self):
        """Test wait for verification code raises when connect fails"""
        service = GmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = False
        with patch.object(service, 'connect', return_value=False):
            with pytest.raises(GmailConnectionError):
                service.wait_for_verification_code("sender@example.com")

    def test_wait_for_verification_code_re_raises_gmail_error(self):
        """Test GmailConnectionError is re-raised"""
        service = GmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = True
        service.email_reader = Mock()
        service.email_reader.get_latest_verification_code.side_effect = GmailConnectionError("conn err")
        with pytest.raises(GmailConnectionError):
            service.wait_for_verification_code("sender@example.com")

    def test_extract_code_from_email_raises_verification_error(self):
        """Test extract_code_from_email raises VerificationCodeExtractionError"""
        service = GmailService()
        service.email_reader = Mock()
        service.email_reader.extract_verification_code_from_subject.side_effect = Exception("no code")
        with pytest.raises(Exception):
            service.extract_code_from_email("subject")

    def test_close_without_email_reader(self):
        """Test close when email_reader is None"""
        service = GmailService(email="test@gmail.com", app_password="pass")
        service.email_reader = None
        service.close()
        assert service._is_connected is False

    def test_close_exception(self):
        """Test close handles exception"""
        service = GmailService(email="test@gmail.com", app_password="pass")
        service._is_connected = True
        service.email_reader = Mock()
        service.email_reader.close.side_effect = Exception("close error")
        service.close()

    def test_context_manager_enter_failure(self):
        """Test context manager raises when connect fails"""
        with patch("scrapper.services.gmail.generic_gmail_service.getEnv") as mock_getEnv:
            mock_getEnv.return_value = None
            with pytest.raises(GmailConnectionError):
                with GmailService():
                    pass

    def test_context_manager_exit(self):
        """Test context manager exit calls close"""
        with patch("scrapper.services.gmail.generic_gmail_service.getEnv") as mock_getEnv:
            mock_getEnv.side_effect = lambda key, default=None: {
                "GMAIL_EMAIL": "test@gmail.com",
                "GMAIL_APP_PASSWORD": "test_password",
            }.get(key, default)
            with patch.object(GmailService, "connect", return_value=True):
                with patch.object(GmailService, "close") as mock_close:
                    with GmailService() as service:
                        pass
                    mock_close.assert_called_once()
