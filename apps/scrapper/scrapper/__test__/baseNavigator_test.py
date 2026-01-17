import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.baseNavigator import BaseNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

class ConcreteNavigator(BaseNavigator):
    def get_total_results(self, *args, **kwargs) -> int:
        return 0
    def click_next_page(self) -> bool:
        return False
    def scroll_jobs_list(self, idx: int):
        pass
    def get_job_data(self):
        return ("","","","","")

class TestBaseNavigator:
    def test_fast_forward_page_logic(self):
        mock_selenium = MagicMock(spec=SeleniumService)
        navigator = ConcreteNavigator(mock_selenium)
        
        # Mock click_next_page on the instance
        navigator.click_next_page = MagicMock()
        navigator.wait_until_page_is_loaded = MagicMock()
        
        # Scenario: Start page 3. Total results enough.
        # fast_forward_page should call click_next_page 2 times (1->2, 2->3).
        # pageExists(3, 100, 10) -> True.
        
        navigator.click_next_page.side_effect = [True, True, False]
        # patch sleep to avoid waiting
        with patch("scrapper.navigator.baseNavigator.sleep"):
             reached_page = navigator.fast_forward_page(start_page=3, total_results=100, jobs_x_page=10)
        
        assert reached_page == 3
        assert navigator.click_next_page.call_count == 2
        assert navigator.wait_until_page_is_loaded.call_count == 2

    def test_fast_forward_page_stops_if_click_fails(self):
        mock_selenium = MagicMock(spec=SeleniumService)
        navigator = ConcreteNavigator(mock_selenium)
        navigator.click_next_page = MagicMock()
        navigator.wait_until_page_is_loaded = MagicMock()
        
        # Scenario: Start page 5. But click_next_page fails after 1st click.
        navigator.click_next_page.side_effect = [True, False]
        
        with patch("scrapper.navigator.baseNavigator.sleep"):
            reached_page = navigator.fast_forward_page(start_page=5, total_results=100, jobs_x_page=10)
        
        # page starts 1. 
        # Loop: page < 5.
        # 1. click -> True. page=2. wait.
        # 2. click -> False. Break.
        # Returns 2.
        
        assert reached_page == 2
        assert navigator.click_next_page.call_count == 2

    def test_fast_forward_page_checks_page_exists(self):
        mock_selenium = MagicMock(spec=SeleniumService)
        navigator = ConcreteNavigator(mock_selenium)
        navigator.click_next_page = MagicMock()
        
        # Scenario: Start page 5. Total results only allow up to page 2.
        # pageExists(5, 20, 10) -> math.ceil(20/10) = 2. 5 < 2 is False.
        # Should not enter loop.
        
        reached_page = navigator.fast_forward_page(start_page=5, total_results=20, jobs_x_page=10)
        
        assert reached_page == 1
        navigator.click_next_page.assert_not_called()
