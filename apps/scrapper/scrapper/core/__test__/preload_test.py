import pytest
from unittest.mock import MagicMock, call
from scrapper.core.scrapper_execution import ScrapperExecution
from scrapper.core.scrapper_scheduler import ScrapperScheduler
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.selenium.seleniumService import SeleniumService

class TestScrapperPreload:
    @pytest.fixture
    def persistence_manager(self):
        pm = MagicMock(spec=PersistenceManager)
        return pm

    @pytest.fixture
    def selenium_service(self):
        return MagicMock(spec=SeleniumService)

    @pytest.fixture
    def scrapper_execution(self, persistence_manager, selenium_service):
        return ScrapperExecution(persistence_manager, selenium_service)

    @pytest.fixture
    def scheduler(self, persistence_manager, selenium_service):
        scheduler = ScrapperScheduler(persistence_manager, selenium_service)
        # Mocking the internal scrapperExecution to verify calls
        scheduler.scrapperExecution = MagicMock(spec=ScrapperExecution)
        return scheduler

    def test_preload_failure_sets_error_in_persistence(self, scrapper_execution, persistence_manager):
        # Setup
        name = "TestScrapper"
        properties = {"preloaded": False, "RUN_IN_TABS": False}
        
        # Mock runScrapper to raise exception
        scrapper_execution.runScrapper = MagicMock(side_effect=Exception("Preload Error"))
        
        # Execute
        result = scrapper_execution.executeScrapperPreload(name, properties)

        # Verify
        assert result is True # Should still return True to continue scheduler loop
        assert properties["preloaded"] is False
        persistence_manager.set_error.assert_called_once()
        args = persistence_manager.set_error.call_args[0]
        assert args[0] == name
        assert "Preload Error" in args[1]

    def test_scheduler_skips_execution_on_preload_failure(self, scheduler):
        # Setup
        scheduler.scrapperExecution.executeScrapperPreload.return_value = True
        scheduler.scrapperExecution.executeScrapper.return_value = True
        
        # We need to simulate the property modification that happens in executeScrapperPreload
        def side_effect_preload(name, properties):
            properties['preloaded'] = False # Simulate failure
            return True
        
        scheduler.scrapperExecution.executeScrapperPreload.side_effect = side_effect_preload

        scrappers_status = [{
            "name": "TestScrapper",
            "properties": {"preloaded": False, "TIMER": 60}, # Requires preload
            "seconds_remaining": 0
        }]
        
        # Execute
        scheduler._execute_scrappers(scrappers_status, False, None)

        # Verify
        scheduler.scrapperExecution.executeScrapperPreload.assert_called_once()
        scheduler.scrapperExecution.executeScrapper.assert_not_called()

    def test_scheduler_executes_on_preload_success(self, scheduler):
        # Setup
        scheduler.scrapperExecution.executeScrapperPreload.return_value = True
        scheduler.scrapperExecution.executeScrapper.return_value = True
        
        def side_effect_preload(name, properties):
            properties['preloaded'] = True # Simulate success
            return True
        
        scheduler.scrapperExecution.executeScrapperPreload.side_effect = side_effect_preload

        scrappers_status = [{
            "name": "TestScrapper",
            "properties": {"preloaded": False, "TIMER": 60},
            "seconds_remaining": 0
        }]
        
        # Execute
        scheduler._execute_scrappers(scrappers_status, False, None)

        # Verify
        scheduler.scrapperExecution.executeScrapperPreload.assert_called_once()
        scheduler.scrapperExecution.executeScrapper.assert_called_once()
