import pytest
from unittest.mock import MagicMock, patch

class TestEmailReader:
    def test_module_imports(self):
        from scrapper.services.gmail import email_reader
        assert hasattr(email_reader, 'EmailReader')
