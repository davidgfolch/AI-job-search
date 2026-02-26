from typing import Any, Dict
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.dateUtil import getSeconds


TIMER = 'timer'
CLOSE_TAB = 'closeTab'
IGNORE_AUTORUN = 'ignoreAutoRun'
DEBUG = 'debug'

SCRAPPERS: Dict[str, Dict[str, Any]] = {
    'Infojobs': {  # first to solve security filter
        TIMER: getSeconds(getEnv('SCRAPPER_INFOJOBS_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('SCRAPPER_INFOJOBS_IGNORE_AUTORUN', False),
        DEBUG: False
    },
    'Tecnoempleo': {  # first to solve security filter
        TIMER: getSeconds(getEnv('SCRAPPER_TECNOEMPLEO_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('SCRAPPER_TECNOEMPLEO_IGNORE_AUTORUN', False),
        DEBUG: False
    },
    'Linkedin': {
        TIMER: getSeconds(getEnv('SCRAPPER_LINKEDIN_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('SCRAPPER_LINKEDIN_IGNORE_AUTORUN', False),
        CLOSE_TAB: True,
        DEBUG: False,
    },
    'Glassdoor': {
        TIMER: getSeconds(getEnv('SCRAPPER_GLASSDOOR_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('SCRAPPER_GLASSDOOR_IGNORE_AUTORUN', False),
        DEBUG: False,
    },
    'Indeed': {
        TIMER: getSeconds(getEnv('SCRAPPER_INDEED_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('SCRAPPER_INDEED_IGNORE_AUTORUN', False),
        DEBUG: False,
    },
}

SCRAPPER_RUN_IN_TABS = getEnvBool('SCRAPPER_RUN_IN_TABS', False)



def get_debug(name):
    return SCRAPPERS[name.capitalize()][DEBUG]
