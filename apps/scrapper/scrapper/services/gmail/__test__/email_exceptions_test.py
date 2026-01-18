import pytest
from scrapper.services.gmail.email_exceptions import (
    GmailConnectionError, EmailNotFoundError, 
    VerificationCodeExtractionError, GmailTimeoutError
)

class TestEmailExceptions:
    def test_gmail_connection_error(self):
        exc = GmailConnectionError("Connection failed")
        assert str(exc) == "Connection failed"
        assert isinstance(exc, Exception)
    
    def test_email_not_found_error(self):
        exc = EmailNotFoundError("Email not found")
        assert str(exc) == "Email not found"
        assert isinstance(exc, Exception)
    
    def test_verification_code_extraction_error(self):
        exc = VerificationCodeExtractionError("Cannot extract code")
        assert str(exc) == "Cannot extract code"
        assert isinstance(exc, Exception)
    
    def test_gmail_timeout_error(self):
        exc = GmailTimeoutError("Timeout")
        assert str(exc) == "Timeout"
        assert isinstance(exc, Exception)

