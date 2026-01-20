import pytest
from unittest.mock import Mock, patch, MagicMock
from scrapper.navigator.indeedNavigator import IndeedNavigator
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.services.gmail.indeed_gmail_service import IndeedGmailService


class TestIndeedNavigator:
    """Test Indeed Navigator functionality"""

    def test_init(self):
        """Test IndeedNavigator initialization"""
        mock_selenium = Mock(spec=SeleniumService)
        navigator = IndeedNavigator(mock_selenium, False)
        assert navigator.selenium == mock_selenium

    @patch("scrapper.navigator.indeedNavigator.sleep")
    @patch("scrapper.navigator.indeedNavigator.IndeedGmailService")
    def test_login(self, mock_gmail_service_class, mock_sleep):
        """Test login flow"""
        # Setup mocks
        mock_selenium = Mock(spec=SeleniumService)
        navigator = IndeedNavigator(mock_selenium, False)
        
        # Mock Gmail service
        mock_gmail_instance = MagicMock(spec=IndeedGmailService)
        mock_gmail_service_class.return_value.__enter__.return_value = mock_gmail_instance
        mock_gmail_instance.wait_for_verification_code.return_value = "123456"

        # Mock Selenium methods
        mock_selenium.waitAndClick_noError.return_value = True
        mock_selenium.getElms.return_value = [] # Return empty list for error check


        # Execute login
        navigator.login()

        # Verify interactions
        mock_selenium.loadPage.assert_called()
        mock_selenium.sendKeys.assert_called()
        mock_selenium.waitAndClick.assert_called()
        
        # Verify 2FA handling
        mock_gmail_instance.wait_for_verification_code.assert_called()
        # Verify we enter the code
        # We can't easily check the arg passed to sendKeys because it's called multiple times
        # but we can verify it was called enough times
        assert mock_selenium.sendKeys.call_count >= 2 

    @patch("scrapper.navigator.indeedNavigator.sleep")
    def test_search(self, mock_sleep):
        """Test search functionality"""
        mock_selenium = Mock(spec=SeleniumService)
        navigator = IndeedNavigator(mock_selenium, False)

        navigator.search("python developer", "Madrid", True, 1, 1)

        # Verify search interactions
        mock_selenium.waitUntil_presenceLocatedElement.assert_called()
        mock_selenium.sendKeys.assert_called()
        mock_selenium.waitAndClick.assert_called()
        mock_selenium.waitUntilPageIsLoaded.assert_called()
        mock_sleep.assert_called()

    def test_get_total_results(self):
        """Test parsing total results"""
        mock_selenium = Mock(spec=SeleniumService)
        navigator = IndeedNavigator(mock_selenium, False)
        
        # Mock generic text return
        mock_selenium.getText.return_value = "1.234 results"
        
        total = navigator.get_total_results("python")
        
        assert total == 1234
