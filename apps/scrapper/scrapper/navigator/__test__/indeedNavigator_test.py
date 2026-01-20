import pytest
from unittest.mock import MagicMock
from scrapper.navigator.indeedNavigator import IndeedNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

class TestIndeedNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock(spec=SeleniumService)
    
    @pytest.fixture
    def navigator(self, mock_selenium):
        return IndeedNavigator(mock_selenium, debug=False)
    
    def test_initialization(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
