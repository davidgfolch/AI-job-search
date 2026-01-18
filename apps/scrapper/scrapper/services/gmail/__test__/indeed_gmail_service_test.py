import pytest
from unittest.mock import MagicMock

class TestIndeedGmailService:
    def test_module_imports(self):
        from scrapper.services.gmail import indeed_gmail_service
        assert hasattr(indeed_gmail_service, 'IndeedGmailService')
