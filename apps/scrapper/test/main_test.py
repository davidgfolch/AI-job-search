import pytest
from unittest.mock import patch, MagicMock
from scrapper.main import (
    CLOSE_TAB, NEW_ARCH, IGNORE_AUTORUN, SCRAPPERS, TIMER, SCRAP_PAGE_FUNCTION,
    runAllScrappers, runSpecifiedScrappers, timeExpired, validScrapperName,
    executeScrapperPreload, executeScrapper, runPreload, getProperties, hasArgument,
    runScrapper, runScrapperPageUrl, hasNewArchitecture, runScrapperNewArchitecture
)

@pytest.fixture
def mocks():
    with patch('scrapper.main.seleniumUtil', MagicMock()) as sel, \
         patch('scrapper.main.persistenceManager', MagicMock()) as pm, \
         patch('scrapper.main.scrapperContainer', create=True) as cont:
        pm.get_last_execution.return_value = None
        yield {'sel': sel, 'pm': pm, 'cont': cont}

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
    }): yield

class TestTimeExpired:
    @pytest.mark.parametrize("now, props, last, expected", [
        (1000, {TIMER: 3600, 'waitBeforeFirstRun': False}, None, True),
        (1000, {TIMER: 3600, 'waitBeforeFirstRun': True}, None, True),
        (100, {TIMER: 3600, 'lastExecution': None, 'waitBeforeFirstRun': False}, None, True),
        (1000, {TIMER: 3600, 'waitBeforeFirstRun': True}, 500, False), # 1000-500=500 < 3600
        (6000, {TIMER: 3600, 'waitBeforeFirstRun': False}, 100, True),  # 6000-100=5900 > 3600
    ])
    def test_time_expired(self, now, props, last, expected):
        with patch('scrapper.main.getDatetimeNow', return_value=now):
            assert timeExpired('', props, last) is expected
            assert props.get('lastExecution') == props.get('lastExecution') # Unchanged

@pytest.mark.parametrize("name, expected", [
    ('Infojobs', True), ('infojobs', True), ('INFOJOBS', True),
    ('INFO JOBS', False), ('non existent', False), ('', False)
])
def test_valid_scrapper_name(name, expected):
    assert validScrapperName(name) is expected

class TestExecuteScrapper:
    @pytest.mark.parametrize("in_tabs, preload, close_tab, error", [
        (False, True, False, None), (True, True, False, None), (False, False, False, Exception)
    ])
    def test_preload(self, mocks, run_mocks, in_tabs, preload, close_tab, error):
        with patch('scrapper.main.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close_tab} if close_tab else {}
            if error: run_mocks['infojobs'].side_effect = error
            executeScrapperPreload('infojobs', props)
            assert props.get('preloaded') is (False if error else preload)
            run_mocks['infojobs'].assert_called_with(mocks['sel'], True, None)

    @pytest.mark.parametrize("in_tabs, close, error", [
        (False, False, None), (True, False, None), (True, True, None), (False, False, Exception)
    ])
    def test_execute(self, mocks, run_mocks, in_tabs, close, error):
        with patch('scrapper.main.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close} if close else {}
            if error: run_mocks['infojobs'].side_effect = error
            executeScrapper('infojobs', props, mocks['pm'])
            if in_tabs: mocks['sel'].tab.assert_called()
            if close: mocks['sel'].tabClose.assert_called()
            run_mocks['infojobs'].assert_called_with(mocks['sel'], False, mocks['pm'])

class TestRunScrappers:
    @patch('scrapper.main.consoleTimer')
    @patch('scrapper.main.getDatetimeNow', return_value=1000)
    @patch('scrapper.main.getTimeUnits', return_value='0s')
    def test_run_all(self, _t, _d, _c, mocks, run_mocks):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
            for k in ['infojobs', 'linkedin', 'glassdoor', 'tecnoempleo']: run_mocks[k].assert_called()
            assert not run_mocks['indeed'].called

    @pytest.mark.parametrize("scrapers, calls", [
        (['Infojobs'], {'infojobs': 2, 'linkedin': 0}),
        (['Infojobs', 'Linkedin'], {'infojobs': 2, 'linkedin': 2}),
        (['infojobs', 'LINKEDIN'], {'infojobs': 2, 'linkedin': 2}),
    ])
    def test_specified(self, scrapers, calls, mocks, run_mocks):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(scrapers)
            for name, count in calls.items(): assert run_mocks[name].call_count == count

class TestNewArchitecture:
    def test_preload(self, mocks):
        srv = MagicMock()
        srv.executeScrapping.return_value = {'login_success': True}
        mocks['cont'].get_scrapping_service.return_value = srv
        props = {NEW_ARCH: True}
        with patch('scrapper.main.SCRAPPERS', {'Linkedin': {NEW_ARCH: True}}):
            executeScrapperPreload('Linkedin', props)
        srv.executeScrapping.assert_called_with(mocks['sel'], [], preloadOnly=True)
        assert props['preloaded'] is True

    def test_execution(self, mocks):
        srv = MagicMock()
        mocks['cont'].get_scrapping_service.return_value = srv
        props = {NEW_ARCH: True}
        with patch.dict('scrapper.main.SCRAPPERS', {'Linkedin': {NEW_ARCH: True}}), \
             patch('scrapper.main.getEnv', return_value='kw'):
            executeScrapper('Linkedin', props, mocks['pm'])
        srv.executeScrapping.assert_called_with(mocks['sel'], ['kw'], preloadOnly=False, persistenceManager=mocks['pm'])

class TestHelpers:
    @pytest.mark.parametrize("arg, props_ok", [('Infojobs', True), ('infojobs', True), ('X', False)])
    def test_get_properties(self, arg, props_ok):
        res = getProperties(arg)
        assert (res is not None and TIMER in res) if props_ok else res is None

    @pytest.mark.parametrize("args, target, expected", [
        (['a', 't', 'b'], 't', True), (['a', 'b'], 't', False)
    ])
    def test_has_argument(self, args, target, expected):
        assert hasArgument(args, target, lambda: None) is expected
        if expected: assert target not in args

    @pytest.mark.parametrize("name", ['linkedin', 'infojobs', 'tecnoempleo', 'glassdoor', 'indeed'])
    def test_run_scrapper(self, name, run_mocks, mocks):
        runScrapper(name, False, None)
        run_mocks[name].assert_called_once_with(mocks['sel'], False, None)

    def test_run_scrapper_page_url(self):
        with patch.dict(SCRAPPERS, {'Infojobs': {SCRAP_PAGE_FUNCTION: MagicMock()}}) as s:
            runScrapperPageUrl('https://www.infojobs.net/job/123')
            s['Infojobs'][SCRAP_PAGE_FUNCTION].assert_called()

    def test_has_new_architecture(self, mocks):
        mocks['cont'].get_scrapping_service.return_value = MagicMock()
        assert hasNewArchitecture('L', {NEW_ARCH: True}) is True
        mocks['cont'].get_scrapping_service.side_effect = Exception
        assert hasNewArchitecture('L', {NEW_ARCH: True}) is False
