import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.scrapper_config import (
    CLOSE_TAB, IGNORE_AUTORUN, SCRAPPERS, TIMER
)
from scrapper.core.scrapper_scheduler import ScrapperScheduler

@pytest.fixture
def mocks():
    sel = MagicMock()
    pm = MagicMock()
    pm.get_last_execution.return_value = None
    return {'sel': sel, 'pm': pm}

@pytest.fixture
def scheduler(mocks):
    return ScrapperScheduler(mocks['pm'], mocks['sel'])

@pytest.fixture
def run_mocks():
    names = ['infojobs', 'linkedin', 'glassdoor', 'tecnoempleo', 'indeed']
    patchers = {name: patch(f'scrapper.{name}.run', MagicMock()) for name in names}
    yield {name: p.start() for name, p in patchers.items()}
    for p in patchers.values(): p.stop()

@pytest.fixture(autouse=True)
def setup_scrappers():
    with patch.dict(SCRAPPERS, {
        'Infojobs': {TIMER: 7200}, 'Linkedin': {TIMER: 3600, CLOSE_TAB: True},
        'Glassdoor': {TIMER: 10800}, 'Tecnoempleo': {TIMER: 7200},
        'Indeed': {TIMER: 10800, IGNORE_AUTORUN: True},
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
    @patch('scrapper.core.scrapper_scheduler.getDatetimeNow', return_value=1000)
    @patch('scrapper.core.scrapper_scheduler.getTimeUnits', return_value='0s')
    def test_run_all(self, _t, _d, _c, scheduler, mocks, run_mocks):
        with patch('scrapper.core.scrapper_scheduler.RUN_IN_TABS', False):
            scheduler.runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
            for k in ['infojobs', 'linkedin', 'glassdoor', 'tecnoempleo']: run_mocks[k].assert_called()
            assert not run_mocks['indeed'].called

    @pytest.mark.parametrize("scrapers, calls", [
        (['Infojobs'], {'infojobs': 2, 'linkedin': 0}),
        (['Infojobs', 'Linkedin'], {'infojobs': 2, 'linkedin': 2}),
        (['infojobs', 'LINKEDIN'], {'infojobs': 2, 'linkedin': 2}),
    ])
    def test_specified(self, scheduler, scrapers, calls, mocks, run_mocks):
        with patch('scrapper.core.scrapper_scheduler.RUN_IN_TABS', False):
            scheduler.runSpecifiedScrappers(scrapers)
            for name, count in calls.items(): assert run_mocks[name].call_count == count

class TestSchedulerHelpers:
    @pytest.mark.parametrize("arg, props_ok", [('Infojobs', True), ('infojobs', True), ('X', False)])
    def test_get_properties(self, scheduler, arg, props_ok):
        res = scheduler.getProperties(arg)
        assert (res is not None and TIMER in res) if props_ok else res is None
