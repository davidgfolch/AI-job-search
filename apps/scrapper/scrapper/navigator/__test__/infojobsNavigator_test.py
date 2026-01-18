import pytest
from unittest.mock import MagicMock
from scrapper.navigator.infojobsNavigator import InfojobsNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

class TestInfojobsNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock(spec=SeleniumService)
    
    @pytest.fixture
    def navigator(self, mock_selenium):
        return InfojobsNavigator(mock_selenium)
    
    def test_initialization(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
