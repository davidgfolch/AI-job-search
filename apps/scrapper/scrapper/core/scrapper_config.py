from typing import Any, Dict
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.dateUtil import getSeconds


TIMER = 'timer'
CLOSE_TAB = 'closeTab'
AUTORUN = 'autoRun'
DEBUG = 'debug'


def _base_config(name: str, autorun: bool = True, debug: bool = False) -> Dict[str, Any]:
    prefix = f'SCRAPPER_{name.upper()}'
    return {
        TIMER: getSeconds(getEnv(f'{prefix}_RUN_CADENCY')),
        AUTORUN: getEnvBool(f'{prefix}_AUTORUN', autorun),
        DEBUG: getEnvBool(f'{prefix}_DEBUG', debug),
    }


SCRAPPERS: Dict[str, Dict[str, Any]] = {
    'Infojobs': _base_config('Infojobs'),    # first to solve security filter
    'Tecnoempleo': _base_config('Tecnoempleo'),  # first to solve security filter
    'Linkedin': {**_base_config('Linkedin'), CLOSE_TAB: True},
    'Glassdoor': _base_config('Glassdoor'),
    'Indeed': _base_config('Indeed'),
}

print(SCRAPPERS)

SCRAPPER_RUN_IN_TABS = getEnvBool('SCRAPPER_RUN_IN_TABS', False)


def get_debug(name):
    return SCRAPPERS[name.capitalize()][DEBUG]
