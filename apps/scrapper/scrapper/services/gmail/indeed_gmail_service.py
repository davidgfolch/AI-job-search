from .generic_gmail_service import GmailService
from commonlib.terminalColor import green


class IndeedGmailService(GmailService):
    """Indeed-specific Gmail service with predefined sender and convenience methods"""

    INDEED_SENDER = "noreply@indeed.com"

    def wait_for_indeed_verification_code(self, timeout: int = 120) -> str:
        """Wait for Indeed verification code with predefined sender"""
        return self.wait_for_verification_code(self.INDEED_SENDER, timeout)

    def get_indeed_verification_code_from_latest_email(self, timeout: int = 120) -> str:
        """Get verification code from latest Indeed email"""
        try:
            if not self._is_connected:
                if not self.connect():
                    raise GmailConnectionError("Failed to connect to Gmail")
            print(f"Waiting for Indeed verification code...")
            code = self.email_reader.get_latest_verification_code(
                self.INDEED_SENDER, timeout
            )
            print(green(f"Indeed verification code received: {code}"))
            return code
        except GmailConnectionError:
            raise
        except Exception as e:
            raise GmailConnectionError(f"Error getting Indeed verification code: {e}")
