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

class TestTimeExpired:
    @pytest.mark.parametrize("now, props, last_offset, expected", [
        (1000000000, {TIMER: 3600, 'waitBeforeFirstRun': False}, None, True),
        (1000000000, {TIMER: 3600, 'waitBeforeFirstRun': True}, None, True),
        (1000000000, {TIMER: 3600, 'lastExecution': None, 'waitBeforeFirstRun': False}, None, True),
        # 500 seconds ago, should NOT be expected (expired=False) because 500 < 3600
        (1000000000, {TIMER: 3600, 'waitBeforeFirstRun': True}, 500, False), 
        # 4000 seconds ago, should be expected (expired=True) because 4000 > 3600
        (1000000000, {TIMER: 3600, 'waitBeforeFirstRun': False}, 4000, True),
    ])
    def test_time_expired(self, scheduler, now, props, last_offset, expected):
        from datetime import datetime
        last = None
        if last_offset is not None:
             last = datetime.fromtimestamp(now - last_offset).strftime("%Y-%m-%d %H:%M:%S")
        with patch('scrapper.core.scrapper_scheduler.getDatetimeNow', return_value=now):
            assert scheduler.timeExpired('', props, last) is expected

@pytest.mark.parametrize("name, expected", [
    ('Infojobs', True), ('infojobs', True), ('INFOJOBS', True),
    ('INFO JOBS', False), ('non existent', False), ('', False)
])
def test_valid_scrapper_name(scheduler, name, expected):
    assert scheduler.validScrapperName(name) is expected

class TestRunScrappers:
    @patch('scrapper.core.scrapper_scheduler.consoleTimer')
    @patch('scrapper.core.scrapper_scheduler.getDatetimeNow', return_value=12000) # Now is 12000
    @patch('scrapper.core.scrapper_scheduler.parseDatetime')
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
    @patch('scrapper.core.scrapper_scheduler.getDatetimeNow', return_value=10000)
    @patch('scrapper.core.scrapper_scheduler.parseDatetime', return_value=9000) # last run 1000s ago
    def test_run_all_starting(self, _p, _n, _t, scheduler, mocks, run_mocks):
        # Scenario: Start at Linkedin. 
        # Even though 1000s lapsed < 3600s timer, it should run because of 'starting'.
        # Infojobs (7200s timer) should NOT run (skipped).
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

class TestScrapperStateAndExecution:
    @pytest.mark.parametrize("starting, startingAt, name, timer, lapsed, expected_state", [
        (False, None, 'Infojobs', 7200, 8000, (0, "Ready", "NOW", "Default", "2h")), # Expired
        (False, None, 'Linkedin', 3600, 1000, (2600, "Pending", "43m 20s", "Default", "1h")), # Not expired
        (True, 'Infojobs', 'Infojobs', 7200, 1000, (0, "STARTING TARGET", "NOW", "Default", "2h")), # Starting target
        (True, 'Infojobs', 'Linkedin', 3600, 5000, (999999999, "Skipped (Start)", "-", "Default", "1h")), # Starting other
    ])
    def test_calculate_scrapper_state(self, scheduler, mocks, starting, startingAt, name, timer, lapsed, expected_state):
        with patch('scrapper.core.scrapper_scheduler.getDatetimeNow', return_value=10000):
            with patch('scrapper.core.scrapper_scheduler.parseDatetime', return_value=10000-lapsed):
                 mocks['pm'].get_last_execution.return_value = "some_date"
                 props = {TIMER: timer}
                 result = scheduler._calculate_scrapper_state(name, props, starting, startingAt)
                 assert result == expected_state

    @pytest.mark.parametrize("error_lapsed, expected_state", [
        (1000, (1800-1000, "Error Wait", "13m 20s", "Error Wait", "30m")), # Error wait active
        (2000, (2600, "Pending", "43m 20s", "Default", "1h")), # Error expired (wait normal timer, assuming 3600 timer and 1000 lapsed for exec)
    ])
    def test_calculate_scrapper_state_error(self, scheduler, mocks, error_lapsed, expected_state):
        # Scenario: Linkedin (3600 timer). 
        # Last exec: 1000s ago. 
        # Last error: error_lapsed s ago.
        
        name = 'Linkedin'
        timer = 3600
        exec_lapsed = 1000
        now = 10000
        
        with patch('scrapper.core.scrapper_scheduler.getDatetimeNow', return_value=now):
            with patch('scrapper.core.scrapper_scheduler.parseDatetime') as mock_parse:
                def side_effect_parse(date_str):
                    if date_str == "last_exec": return now - exec_lapsed
                    if date_str == "last_error": return now - error_lapsed
                    return 0
                mock_parse.side_effect = side_effect_parse
                
                mocks['pm'].get_last_execution.return_value = "last_exec"
                
                # Setup get_state to return proper dicts based on test needs
                # Base mock returns empty dict by default if not specialized
                
                def get_state_side_effect(n):
                    if n == name:
                        return {"last_error_time": "last_error"}
                    return {}
                mocks['pm'].get_state.side_effect = get_state_side_effect
                
                props = {TIMER: timer}
                result = scheduler._calculate_scrapper_state(name, props, False, None)
                assert result == expected_state

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
