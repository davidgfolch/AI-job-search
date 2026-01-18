import pytest
from unittest.mock import MagicMock
from scrapper.navigator.glassdoorNavigator import GlassdoorNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

class TestGlassdoorNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock(spec=SeleniumService)
    
    @pytest.fixture
    def navigator(self, mock_selenium):
        return GlassdoorNavigator(mock_selenium)
    
    def test_initialization(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
    
    def test_check_easy_apply_returns_boolean(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert navigator.check_easy_apply() is False
        mock_selenium.getElms.return_value = [MagicMock()]
        assert navigator.check_easy_apply() is True
