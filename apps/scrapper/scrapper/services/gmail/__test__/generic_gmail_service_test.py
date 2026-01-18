import pytest
from unittest.mock import MagicMock

class TestGenericGmailService:
    def test_module_imports(self):
        from scrapper.services.gmail import generic_gmail_service
        assert hasattr(generic_gmail_service, 'GmailService')
