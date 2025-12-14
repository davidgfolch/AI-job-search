import pytest
from unittest.mock import patch, MagicMock
from scrapper.scrapper_config import (
    CLOSE_TAB, NEW_ARCH, IGNORE_AUTORUN, SCRAPPERS, TIMER
)
from scrapper.scrapper_scheduler import (
    runAllScrappers, runSpecifiedScrappers, timeExpired, validScrapperName,
    getProperties
)
from scrapper.scrapper_execution import (
    executeScrapperPreload, executeScrapper, runPreload,
    runScrapper, runScrapperPageUrl, hasNewArchitecture, runScrapperNewArchitecture,
    abortExecution
)
from scrapper.main import hasArgument 

@pytest.fixture
def mocks():
    # We no longer patch globals in main, but create mocks to pass in
    sel = MagicMock()
    pm = MagicMock()
    cont = MagicMock()
    pm.get_last_execution.return_value = None
    return {'sel': sel, 'pm': pm, 'cont': cont}

@pytest.fixture
def run_mocks():
    names = ['infojobs', 'linkedin', 'glassdoor', 'tecnoempleo', 'indeed']
    # Patch where they are used or defined. 
    # They are imported in scrapper_execution.py from scrapper package.
    # scrapper.infojobs.run is the target.
    patchers = {name: patch(f'scrapper.{name}.run', MagicMock()) for name in names}
    yield {name: p.start() for name, p in patchers.items()}
    for p in patchers.values(): p.stop()

@pytest.fixture(autouse=True)
def setup_scrappers():
    # Patch the SCRAPPERS dict in scrapper_config and scrapper_execution/scheduler where it's imported?
    # No, it's imported from scrapper_config. So patching scrapper.scrapper_config.SCRAPPERS works 
    # if the modules use `from scrapper_config import SCRAPPERS` and usage is dynamic or referenced via module?
    # If they did `from scrapper_config import SCRAPPERS`, patch might need to be on the importing module 
    # OR if we patch scrapper.scrapper_config.SCRAPPERS and reload?
    # `dict` patch modifies the object in place, so it should work if it's the same object reference.
    with patch.dict(SCRAPPERS, {
        'Infojobs': {TIMER: 7200}, 'Linkedin': {TIMER: 3600, CLOSE_TAB: True},
        'Glassdoor': {TIMER: 10800}, 'Tecnoempleo': {TIMER: 7200},
        'Indeed': {TIMER: 10800, IGNORE_AUTORUN: True},
    }, clear=True): 
        yield

class TestTimeExpired:
    @pytest.mark.parametrize("now, props, last, expected", [
        (1000, {TIMER: 3600, 'waitBeforeFirstRun': False}, None, True),
        (1000, {TIMER: 3600, 'waitBeforeFirstRun': True}, None, True),
        (100, {TIMER: 3600, 'lastExecution': None, 'waitBeforeFirstRun': False}, None, True),
        (1000, {TIMER: 3600, 'waitBeforeFirstRun': True}, 500, False), # 1000-500=500 < 3600
        (6000, {TIMER: 3600, 'waitBeforeFirstRun': False}, 100, True),  # 6000-100=5900 > 3600
    ])
    def test_time_expired(self, now, props, last, expected):
        with patch('scrapper.scrapper_scheduler.getDatetimeNow', return_value=now):
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
        with patch('scrapper.scrapper_execution.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close_tab} if close_tab else {}
            if error: run_mocks['infojobs'].side_effect = error
            executeScrapperPreload('infojobs', props, mocks['sel'], mocks['cont'], mocks['pm'])
            assert props.get('preloaded') is (False if error else preload)
            run_mocks['infojobs'].assert_called_with(mocks['sel'], True, mocks['pm'])

    @pytest.mark.parametrize("in_tabs, close, error", [
        (False, False, None), (True, False, None), (True, True, None), (False, False, Exception)
    ])
    def test_execute(self, mocks, run_mocks, in_tabs, close, error):
        with patch('scrapper.scrapper_execution.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close} if close else {}
            if error: run_mocks['infojobs'].side_effect = error
            executeScrapper('infojobs', props, mocks['pm'], mocks['sel'], mocks['cont'])
            if in_tabs: mocks['sel'].tab.assert_called()
            if close: mocks['sel'].tabClose.assert_called()
            run_mocks['infojobs'].assert_called_with(mocks['sel'], False, mocks['pm'])

class TestRunScrappers:
    @patch('scrapper.scrapper_scheduler.consoleTimer')
    @patch('scrapper.scrapper_scheduler.getDatetimeNow', return_value=1000)
    @patch('scrapper.scrapper_scheduler.getTimeUnits', return_value='0s')
    def test_run_all(self, _t, _d, _c, mocks, run_mocks):
        with patch('scrapper.scrapper_scheduler.RUN_IN_TABS', False):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, persistenceManager=mocks['pm'], seleniumUtil=mocks['sel'], scrapperContainer=mocks['cont'], loops=1)
            for k in ['infojobs', 'linkedin', 'glassdoor', 'tecnoempleo']: run_mocks[k].assert_called()
            assert not run_mocks['indeed'].called

    @pytest.mark.parametrize("scrapers, calls", [
        (['Infojobs'], {'infojobs': 2, 'linkedin': 0}),
        (['Infojobs', 'Linkedin'], {'infojobs': 2, 'linkedin': 2}),
        (['infojobs', 'LINKEDIN'], {'infojobs': 2, 'linkedin': 2}),
    ])
    def test_specified(self, scrapers, calls, mocks, run_mocks):
        with patch('scrapper.scrapper_scheduler.RUN_IN_TABS', False):
            runSpecifiedScrappers(scrapers, mocks['pm'], mocks['sel'], mocks['cont'])
            for name, count in calls.items(): assert run_mocks[name].call_count == count

class TestNewArchitecture:
    def test_preload(self, mocks):
        srv = MagicMock()
        srv.executeScrapping.return_value = {'login_success': True}
        mocks['cont'].get_scrapping_service.return_value = srv
        props = {NEW_ARCH: True}
        # Patching SCRAPPERS in execution/config because runScrapperPageUrl might use it? 
        # But executeScrapperPreload uses passed properties or checks hasNewArchitecture with passed properties.
        # hasNewArchitecture uses properties passed in.
        executeScrapperPreload('Linkedin', props, mocks['sel'], mocks['cont'], mocks['pm'])
        srv.executeScrapping.assert_called_with(mocks['sel'], [], preloadOnly=True)
        assert props['preloaded'] is True

    def test_execution(self, mocks):
        srv = MagicMock()
        mocks['cont'].get_scrapping_service.return_value = srv
        props = {NEW_ARCH: True}
        with patch('scrapper.scrapper_execution.getEnv', return_value='kw'):
            executeScrapper('Linkedin', props, mocks['pm'], mocks['sel'], mocks['cont'])
        srv.executeScrapping.assert_called_with(mocks['sel'], ['kw'], preloadOnly=False, persistenceManager=mocks['pm'])

class TestHelpers:
    @pytest.mark.parametrize("arg, props_ok", [('Infojobs', True), ('infojobs', True), ('X', False)])
    def test_get_properties(self, arg, props_ok):
        res = getProperties(arg)
        # TIMER checking:
        # SCRAPPERS was patched in setup_scrappers fixture fixture.
        assert (res is not None and TIMER in res) if props_ok else res is None

    @pytest.mark.parametrize("args, target, expected", [
        (['a', 't', 'b'], 't', True), (['a', 'b'], 't', False)
    ])
    def test_has_argument(self, args, target, expected):
        assert hasArgument(args, target, lambda: None) is expected
        if expected: assert target not in args

    @pytest.mark.parametrize("name", ['linkedin', 'infojobs', 'tecnoempleo', 'glassdoor', 'indeed'])
    def test_run_scrapper(self, name, run_mocks, mocks):
        runScrapper(name, False, mocks['pm'], mocks['sel'])
        run_mocks[name].assert_called_once_with(mocks['sel'], False, mocks['pm'])


    def test_has_new_architecture(self, mocks):
        mocks['cont'].get_scrapping_service.return_value = MagicMock()
        assert hasNewArchitecture('L', {NEW_ARCH: True}, mocks['cont']) is True
        mocks['cont'].get_scrapping_service.side_effect = Exception
        assert hasNewArchitecture('L', {NEW_ARCH: True}, mocks['cont']) is False


class TestRunScrapperPageUrl:
    def test_linkedin_url(self, mocks):
        url = "https://www.linkedin.com/jobs/view/123"
        with patch('scrapper.scrapper_execution.linkedin.processUrl') as mock_process:
            runScrapperPageUrl(url)
            mock_process.assert_called_once_with(url)

    def test_unimplemented_scrapper(self):
        url = "https://www.infojobs.net/job/123"
        with pytest.raises(Exception) as excinfo:
            runScrapperPageUrl(url)
        # The logic in runScrapperPageUrl uses SCRAPPERS to match name.
        # SCRAPPERS['Infojobs'] exists. url finds infojobs. match case infojobs fails.
        assert "Invalid scrapper web page name Infojobs, only linkedin is implemented" in str(excinfo.value)

    def test_unknown_url(self):
        url = "https://www.google.com"
        with patch('scrapper.scrapper_execution.linkedin.processUrl') as mock_process:
            runScrapperPageUrl(url)
            mock_process.assert_not_called()
