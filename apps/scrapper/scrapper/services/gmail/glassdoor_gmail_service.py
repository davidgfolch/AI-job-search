from .generic_gmail_service import GmailService
from .email_exceptions import GmailConnectionError
from commonlib.terminalColor import green


class GlassdoorGmailService(GmailService):
    """Glassdoor-specific Gmail service with predefined sender for Indeed OTP login"""

    GLASSDOOR_SENDER = "login@indeed.com"

    def wait_for_glassdoor_verification_code(self, timeout: int = 180) -> str:
        """Wait for Glassdoor/Indeed OTP verification code with predefined sender"""
        return self.wait_for_verification_code(self.GLASSDOOR_SENDER, timeout)
