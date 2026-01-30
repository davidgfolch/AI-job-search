import pytest
from unittest.mock import MagicMock

class TestElementService:
    def test_module_imports(self):
        from scrapper.services.selenium import element_service
        assert hasattr(element_service, 'ElementService')
