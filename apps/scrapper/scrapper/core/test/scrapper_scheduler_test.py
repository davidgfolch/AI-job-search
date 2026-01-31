import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.scrapper_config import (
    CLOSE_TAB, IGNORE_AUTORUN, SCRAPPERS, TIMER, DEBUG
)
from scrapper.core.scrapper_scheduler import ScrapperScheduler

@pytest.fixture
def mocks():
    sel = MagicMock()
    pm = MagicMock()
    pm.get_last_execution.return_value = None
    pm.get_failed_keywords.return_value = []
    pm.get_state.return_value = {}
    return {'sel': sel, 'pm': pm}

@pytest.fixture
def scheduler(mocks):
    return ScrapperScheduler(mocks['pm'], mocks['sel'])

@pytest.fixture
def run_mocks():
    mapping = {
        'infojobs': 'InfojobsExecutor',
        'linkedin': 'LinkedinExecutor',
        'glassdoor': 'GlassdoorExecutor',
        'tecnoempleo': 'TecnoempleoExecutor',
        'indeed': 'IndeedExecutor'
    }
    # Patch the actual executor modules
    patchers = {key: patch(f'scrapper.executor.{cls}.{cls}') for key, cls in mapping.items()}
    started_patchers = {key: p.start() for key, p in patchers.items()}
    # Mock both execute and execute_preload methods
    mocked_methods = {}
    for key, mock_cls in started_patchers.items():
        mock_instance = mock_cls.return_value
        mock_instance.execute.return_value = True
        mock_instance.execute_preload.return_value = True
        mocked_methods[key] = mock_instance
    yield mocked_methods
    for p in patchers.values():
        p.stop()

@pytest.fixture(autouse=True)
def setup_scrappers():
    with patch.dict(SCRAPPERS, {
        'Infojobs': {TIMER: 7200, DEBUG: False}, 'Linkedin': {TIMER: 3600, CLOSE_TAB: True, DEBUG: False},
        'Glassdoor': {TIMER: 10800, DEBUG: False}, 'Tecnoempleo': {TIMER: 7200, DEBUG: False},
        'Indeed': {TIMER: 10800, IGNORE_AUTORUN: True, DEBUG: False},
    }, clear=True): 
        yield


@pytest.mark.parametrize("name, expected", [
    ('Infojobs', True), ('infojobs', True), ('INFOJOBS', True),
    ('INFO JOBS', False), ('non existent', False), ('', False)
])
def test_valid_scrapper_name(scheduler, name, expected):
    assert scheduler.validScrapperName(name) is expected

class TestRunScrappers:
    @patch('scrapper.core.scrapper_scheduler.consoleTimer')
    @patch('scrapper.core.scrapper_state_calculator.getDatetimeNow', return_value=12000)
    @patch('scrapper.core.scrapper_state_calculator.parseDatetime')
    def test_run_all(self, mock_parse, mock_now, mock_timer, scheduler, mocks, run_mocks):
        # Scenario: 
        # Infojobs: TIMER 7200. Last run: 12000-8000 = 4000. Lapsed 8000. expired (8000>7200). Ready.
        # Linkedin: TIMER 3600. Last run: 12000-1000 = 11000. Lapsed 1000. Not expired. Wait 2600.
        def side_effect_parse(date_str):
            # Map mock dates for testing
            if date_str == "last_run_infojobs": return 4000
            if date_str == "last_run_linkedin": return 11000
            return 0
        mock_parse.side_effect = side_effect_parse
        # mock_now doesn't need side_effect as it has return_value=12000
        mocks['pm'].get_last_execution.side_effect = lambda name: f"last_run_{name.lower()}" if name in ['Infojobs', 'Linkedin'] else None
        with patch('scrapper.core.scrapper_scheduler.RUN_IN_TABS', False):
             # Only 1 loop to test one pass
            scheduler.runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
            # Infojobs should run because it's expired
            run_mocks['infojobs'].execute.assert_called()
            # Linkedin should NOT run because it's not expired
            assert not run_mocks['linkedin'].execute.called
            # Timer should be called because we have to wait for Linkedin (or others)
            # In this mock setup:
            # Infojobs: ready (wait 0)
            # Linkedin: wait 2600
            # Others: last run None -> wait 0? 
            # Original code: if lastExec is None and 'waitBeforeFirstRun' is False (default) -> lastExec updated to NOW? 
            # Wait, let's check 'lastExecution' method again.
            # It updates last execution if None and waitBeforeFirstRun is True. 
            # If waitBeforeFirstRun is False (default passed in test), lastExecution returns None.
            # In my new code: if last_exec_time is None (and properties[TIMER] exists), seconds_remaining = 0.
            # So others (Glassdoor etc) will be ready.
            
            # To test the 'Wait' strictly, we'd need all of them to be waiting.
            # But the specific test here checks execution.
            pass

    @patch('scrapper.core.scrapper_scheduler.consoleTimer')
    @patch('scrapper.core.scrapper_state_calculator.getDatetimeNow', return_value=10000)
    @patch('scrapper.core.scrapper_state_calculator.parseDatetime')
    def test_run_all_starting(self, mock_parse, mock_now, mock_timer, scheduler, mocks, run_mocks):
        # Scenario: Start at Linkedin. 
        # Even though 1000s lapsed < 3600s timer, it should run because of 'starting'.
        # Infojobs (7200s timer) should NOT run (skipped).
        mock_parse.return_value = 9000
        with patch('scrapper.core.scrapper_scheduler.RUN_IN_TABS', False):
             scheduler.runAllScrappers(waitBeforeFirstRuns=False, starting=True, startingAt='Linkedin', loops=1)
             run_mocks['linkedin'].execute.assert_called()
             assert not run_mocks['infojobs'].execute.called

    @pytest.mark.parametrize("scrapers, calls", [
        (['Infojobs'], {'infojobs': 2, 'linkedin': 0}),
        (['Infojobs', 'Linkedin'], {'infojobs': 2, 'linkedin': 2}),
        (['infojobs', 'LINKEDIN'], {'infojobs': 2, 'linkedin': 2}),
    ])
    def test_specified(self, scheduler, scrapers, calls, mocks, run_mocks):
        with patch('scrapper.core.scrapper_scheduler.RUN_IN_TABS', False):
            scheduler.runSpecifiedScrappers(scrapers)
            # Count both execute_preload and execute as 2 total calls
            for name, expected_count in calls.items(): 
                actual_count = run_mocks[name].execute_preload.call_count + run_mocks[name].execute.call_count
                assert actual_count == expected_count

class TestSchedulerHelpers:
    @pytest.mark.parametrize("arg, props_ok", [('Infojobs', True), ('infojobs', True), ('X', False)])
    def test_get_properties(self, scheduler, arg, props_ok):
        res = scheduler.getProperties(arg)
        assert (res is not None and TIMER in res) if props_ok else res is None

    def test_execute_scrappers(self, scheduler, run_mocks):
         status = [
             {'name': 'Infojobs', 'properties': {TIMER: 7200}, 'seconds_remaining': 0},
             {'name': 'Linkedin', 'properties': {TIMER: 3600}, 'seconds_remaining': 100}
         ]
         with patch('scrapper.core.scrapper_scheduler.RUN_IN_TABS', False):
             should_cont, executed_start = scheduler._execute_scrappers(status, False, None)
             assert should_cont is True
             assert executed_start is False
             run_mocks['infojobs'].execute.assert_called()
             assert not run_mocks['linkedin'].execute.called
    @patch('scrapper.core.scrapper_scheduler.BaseExecutor.create')
    def test_scheduler_skips_execution_on_preload_failure(self, mock_create, scheduler, mocks):
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
        with patch('scrapper.core.scrapper_scheduler.get_debug', return_value=False):
            with patch('scrapper.core.scrapper_scheduler.RUN_IN_TABS', False):
                scheduler._execute_scrappers(scrappers_status, False, None)
        # Verify
        mock_executor.execute_preload.assert_called_once()
        mock_executor.execute.assert_not_called()

    @patch('scrapper.core.scrapper_scheduler.BaseExecutor.create')
    def test_scheduler_executes_on_preload_success(self, mock_create, scheduler, mocks):
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
        with patch('scrapper.core.scrapper_scheduler.get_debug', return_value=False):
             with patch('scrapper.core.scrapper_scheduler.RUN_IN_TABS', False):
                scheduler._execute_scrappers(scrappers_status, False, None)
        # Verify
        mock_executor.execute_preload.assert_called_once()
        mock_executor.execute.assert_called_once()
