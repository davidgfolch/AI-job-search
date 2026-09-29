import time
from typing import Optional
from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger
from .email_reader import EmailReader
from .email_exceptions import (
    GmailConnectionError,
    EmailNotFoundError,
    VerificationCodeExtractionError,
    GmailTimeoutError,
)

logger = get_logger("scrapper.generic_gmail_service")


class GmailService:
    def __init__(self, email: str = None, app_password: str = None):
        self.email = email or getEnv("GMAIL_EMAIL")
        self.app_password = app_password or getEnv("GMAIL_APP_PASSWORD")
        self.email_reader = None
        self._is_connected = False

    def connect(self) -> bool:
        """Connect to Gmail service"""
        try:
            if not self.email or not self.app_password:
                raise GmailConnectionError("Gmail email or app password not provided")
            self.email_reader = EmailReader(self.email, self.app_password)
            self.email_reader.connect()
            self._is_connected = True
            logger.info("gmail.connected", has_credentials=True)
            return True
        except Exception as e:
            logger.error("gmail.connect_failed", error=str(e))
            return False

    def wait_for_verification_code(self, sender_filter: str, timeout: int = 120) -> str:
        try:
            if not self._is_connected:
                if not self.connect():
                    raise GmailConnectionError("Failed to connect to Gmail")
            logger.info("gmail.code_wait_started", timeout=timeout, sender_present=bool(sender_filter))
            code = self.email_reader.get_latest_verification_code(
                sender_filter, timeout
            )
            logger.info("gmail.code_received", code_length=len(code))
            return code
        except GmailConnectionError:
            raise
        except Exception as e:
            raise GmailConnectionError(f"Error getting verification code: {e}")

    def extract_code_from_email(self, subject: str) -> str:
        try:
            return self.email_reader.extract_verification_code_from_subject(subject)
        except:
            raise VerificationCodeExtractionError("No verification code found in email subject")

    def is_connected(self) -> bool:
        """Check if Gmail service is connected"""
        return self._is_connected

    def close(self):
        """Close Gmail connection"""
        try:
            if self.email_reader:
                self.email_reader.close()
                self._is_connected = False
                logger.info("gmail.closed")
        except Exception as e:
            logger.error("gmail.close_failed", error=str(e))

    def __enter__(self):
        """Context manager entry"""
        if self.connect():
            return self
        else:
            raise GmailConnectionError("Failed to initialize Gmail service")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
