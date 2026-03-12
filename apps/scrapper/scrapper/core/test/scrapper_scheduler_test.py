import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.scrapper_config import (
    CLOSE_TAB, AUTORUN, SCRAPPERS, TIMER, DEBUG
)
from scrapper.core.scrapper_scheduler import ScrapperScheduler

@pytest.fixture
def mocks():
    pm = MagicMock()
    pm.get_last_execution.return_value = None
    pm.get_failed_keywords.return_value = []
    pm.get_state.return_value = {}
    return {'sel': MagicMock(), 'pm': pm}

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
    patchers = {key: patch(f'scrapper.executor.{cls}.{cls}') for key, cls in mapping.items()}
    started = {key: p.start() for key, p in patchers.items()}
    
    methods = {}
    for key, mock_cls in started.items():
        mock_instance = mock_cls.return_value
        mock_instance.execute.return_value = True
        mock_instance.execute_preload.return_value = True
        methods[key] = mock_instance
        
    yield methods
    for p in patchers.values(): p.stop()

@pytest.fixture(autouse=True)
def setup_scrappers():
    val = {
        'Infojobs': {TIMER: 7200, AUTORUN: True, DEBUG: False},
        'Linkedin': {TIMER: 3600, AUTORUN: True, CLOSE_TAB: True, DEBUG: False},
        'Glassdoor': {TIMER: 10800, AUTORUN: True, DEBUG: False},
        'Tecnoempleo': {TIMER: 7200, AUTORUN: True, DEBUG: False},
        'Indeed': {TIMER: 10800, AUTORUN: False, DEBUG: False},
    }
    with patch.dict(SCRAPPERS, val, clear=True): 
        yield

@pytest.mark.parametrize("name, expected", [
    ('Infojobs', True), ('infojobs', True), ('INFOJOBS', True),
    ('INFO JOBS', False), ('', False)
])
def test_valid_scrapper_name(scheduler, name, expected):
    assert scheduler.validScrapperName(name) is expected

@pytest.mark.parametrize("arg, props_ok", [('Infojobs', True), ('infojobs', True), ('X', False)])
def test_get_properties(scheduler, arg, props_ok):
    res = scheduler.getProperties(arg)
    assert (res is not None and TIMER in res) if props_ok else res is None

@pytest.mark.parametrize("starting, start_at, p_date, info_called, link_called", [
    (False, None, lambda d: 4000 if 'infojobs' in d else 11000, True, False),
    (True, 'Linkedin', lambda d: 9000, False, True)
])
@patch('scrapper.core.scrapper_scheduler.consoleTimer')
@patch('scrapper.core.scrapper_state_calculator.getDatetimeNow', return_value=12000)
@patch('scrapper.core.scrapper_state_calculator.parseDatetime')
@patch('scrapper.core.scrapper_scheduler.SCRAPPER_RUN_IN_TABS', False)
def test_run_scenarios(mock_parse, mock_now, mock_timer, scheduler, mocks, run_mocks, starting, start_at, p_date, info_called, link_called):
    mock_parse.side_effect = p_date
    mocks['pm'].get_last_execution.side_effect = lambda n: f"last_run_{n.lower()}" if n in ['Infojobs', 'Linkedin'] else None
    
    scheduler.runAllScrappers(waitBeforeFirstRuns=False, starting=starting, startingAt=start_at, loops=1)
    
    assert run_mocks['infojobs'].execute.called == info_called
    assert run_mocks['linkedin'].execute.called == link_called

@pytest.mark.parametrize("scrapers, expected_calls", [
    (['Infojobs'], {'infojobs': 2, 'linkedin': 0}),
    (['Infojobs', 'Linkedin'], {'infojobs': 2, 'linkedin': 2}),
    (['infojobs', 'LINKEDIN'], {'infojobs': 2, 'linkedin': 2})
])
@patch('scrapper.core.scrapper_scheduler.SCRAPPER_RUN_IN_TABS', False)
def test_specified(scheduler, scrapers, expected_calls, run_mocks):
    scheduler.runSpecifiedScrappers(scrapers)
    for name, expected_count in expected_calls.items(): 
        actual_count = run_mocks[name].execute_preload.call_count + run_mocks[name].execute.call_count
        assert actual_count == expected_count

@patch('scrapper.core.scrapper_scheduler.SCRAPPER_RUN_IN_TABS', False)
def test_execute_scrappers(scheduler, run_mocks):
    status = [
        {'name': 'Infojobs', 'properties': {TIMER: 7200}, 'seconds_remaining': 0},
        {'name': 'Linkedin', 'properties': {TIMER: 3600}, 'seconds_remaining': 100}
    ]
    should_cont, exec_start = scheduler._execute_scrappers(status, False, None)
    
    assert should_cont is True and exec_start is False
    run_mocks['infojobs'].execute.assert_called()
    assert not run_mocks['linkedin'].execute.called

@pytest.mark.parametrize("preload_res, preloaded_val, expect_cont, expect_exec", [
    (True, False, None, False),   # skips on preload failure
    (False, None, False, False),  # returns false on preload error
    (True, True, None, True),     # executes on preload success
])
@patch('scrapper.core.scrapper_scheduler.get_debug', return_value=False)
@patch('scrapper.core.scrapper_scheduler.SCRAPPER_RUN_IN_TABS', False)
@patch('scrapper.core.scrapper_scheduler.create_executor')
def test_preload_execution(mock_create, mock_debug, scheduler, preload_res, preloaded_val, expect_cont, expect_exec):
    mock_ex = MagicMock()
    mock_create.return_value = mock_ex
    
    def side_effect(props):
        if preloaded_val is not None: props['preloaded'] = preloaded_val
        return preload_res
        
    mock_ex.execute_preload.side_effect = side_effect
    status = [{"name": "TestScrapper", "properties": {"preloaded": False, "TIMER": 60}, "seconds_remaining": 0}]
    
    should_cont, exec_start = scheduler._execute_scrappers(status, False, None)
    
    if expect_cont is not None: assert should_cont is expect_cont
    mock_ex.execute_preload.assert_called_once()
    assert mock_ex.execute.called == expect_exec
