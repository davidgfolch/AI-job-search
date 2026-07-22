from typing import Any, Dict
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.dateUtil import getSeconds


TIMER = 'timer'
CLOSE_TAB = 'closeTab'
AUTORUN = 'autoRun'
DEBUG = 'debug'
BROWSER = 'browser'


def _base_config(name: str, autorun: bool = True, debug: bool = False) -> Dict[str, Any]:
    prefix = f'SCRAPPER_{name.upper()}'
    return {
        TIMER: getSeconds(getEnv(f'{prefix}_RUN_CADENCY')),
        AUTORUN: getEnvBool(f'{prefix}_AUTORUN', autorun),
        DEBUG: getEnvBool(f'{prefix}_DEBUG', debug),
        BROWSER: getEnv(f'{prefix}_BROWSER', 'chrome').lower(),
    }


SCRAPPERS: Dict[str, Dict[str, Any]] = {
    'Linkedin': {**_base_config('Linkedin'), CLOSE_TAB: True},
    'Infojobs': _base_config('Infojobs'),    # first to solve security filter
    'Tecnoempleo': _base_config('Tecnoempleo'),  # first to solve security filter
    'Glassdoor': _base_config('Glassdoor'),
    'Indeed': _base_config('Indeed'),
}

print(SCRAPPERS)

SCRAPPER_RUN_IN_TABS = getEnvBool('SCRAPPER_RUN_IN_TABS', False)
STALE_THRESHOLD_HOURS = int(getEnv('SCRAPPER_STATE_STALE_THRESHOLD_HOURS', '48'))


def get_debug(name):
    return SCRAPPERS[name.capitalize()][DEBUG]
