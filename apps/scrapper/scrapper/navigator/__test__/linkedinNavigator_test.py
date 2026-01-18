import pytest
from unittest.mock import MagicMock
from scrapper.navigator.linkedinNavigator import LinkedinNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

class TestLinkedinNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock(spec=SeleniumService)
    
    @pytest.fixture
    def navigator(self, mock_selenium):
        return LinkedinNavigator(mock_selenium)
    
    def test_initialization(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
