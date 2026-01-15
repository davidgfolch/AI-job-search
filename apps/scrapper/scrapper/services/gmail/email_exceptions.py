class GmailConnectionError(Exception):
    """Exception raised when Gmail connection fails"""
    pass


class EmailNotFoundError(Exception):
    """Exception raised when expected email is not found"""
    pass


class VerificationCodeExtractionError(Exception):
    """Exception raised when verification code cannot be extracted from email"""
    pass


class GmailTimeoutError(Exception):
    """Exception raised when Gmail operation times out"""
    pass
