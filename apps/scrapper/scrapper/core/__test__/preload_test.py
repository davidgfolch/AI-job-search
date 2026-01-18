import pytest
from unittest.mock import MagicMock, call, patch
from scrapper.core.scrapper_scheduler import ScrapperScheduler
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.executor.BaseExecutor import BaseExecutor

class TestScrapperPreload:
    @pytest.fixture
    def persistence_manager(self):
        pm = MagicMock(spec=PersistenceManager)
        return pm

    @pytest.fixture
    def selenium_service(self):
        return MagicMock(spec=SeleniumService)

    @pytest.fixture
    def scheduler(self, persistence_manager, selenium_service):
        return ScrapperScheduler(persistence_manager, selenium_service)

    def test_preload_failure_sets_error_in_persistence(self, persistence_manager, selenium_service):
        # Setup - patch the executor to test execute_preload directly
        name = "infojobs"
        properties = {"preloaded": False}
        
        with patch('scrapper.executor.InfojobsExecutor.InfojobsExecutor') as mock_executor_cls:
            mock_executor = MagicMock()
            mock_executor.site_name = "INFOJOBS"
            mock_executor.site_name_key = "Infojobs"
            mock_executor.selenium_service = selenium_service
            mock_executor.persistence_manager = persistence_manager
            mock_executor_cls.return_value = mock_executor
            # Call run() to trigger exception
            mock_executor.run.side_effect = Exception("Preload Error")
            # Import execute_preload method from BaseExecutor and bind it
            result = BaseExecutor.execute_preload(mock_executor, properties)
            
            # Verify
            assert result is True
            assert properties["preloaded"] is False
            persistence_manager.set_error.assert_called_once()
            args = persistence_manager.set_error.call_args[0]
            assert args[0] == "Infojobs"
            assert "Preload Error" in args[1]

    def test_scheduler_skips_execution_on_preload_failure(self, scheduler, persistence_manager):
        # Setup - mock BaseExecutor.create to return mock instances
        with patch('scrapper.core.scrapper_scheduler.BaseExecutor.create') as mock_create:
            mock_executor = MagicMock()
            mock_create.return_value = mock_executor
            
            # Simulate preload failure
            def side_effect_preload(properties):
                properties['preloaded'] = False
                return True
            
            mock_executor.execute_preload.side_effect = side_effect_preload
            
            scrappers_status = [{
                "name": "TestScrapper",
                "properties": {"preloaded": False, "TIMER": 60},
                "seconds_remaining": 0
            }]
            
            # Execute
            scheduler._execute_scrappers(scrappers_status, False, None)

            # Verify
            mock_executor.execute_preload.assert_called_once()
            mock_executor.execute.assert_not_called()

    def test_scheduler_executes_on_preload_success(self, scheduler, persistence_manager):
        # Setup
        with patch('scrapper.core.scrapper_scheduler.BaseExecutor.create') as mock_create:
            mock_executor = MagicMock()
            mock_create.return_value = mock_executor
            
            def side_effect_preload(properties):
                properties['preloaded'] = True
                return True
            
            mock_executor.execute_preload.side_effect = side_effect_preload
            mock_executor.execute.return_value = True

            scrappers_status = [{
                "name": "TestScrapper",
                "properties": {"preloaded": False, "TIMER": 60},
                "seconds_remaining": 0
            }]
            
            # Execute
            scheduler._execute_scrappers(scrappers_status, False, None)

            # Verify
            mock_executor.execute_preload.assert_called_once()
            mock_executor.execute.assert_called_once()
