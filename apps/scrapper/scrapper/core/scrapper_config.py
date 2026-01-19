from typing import Any, Dict
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.dateUtil import getSeconds


TIMER = 'timer'
CLOSE_TAB = 'closeTab'
IGNORE_AUTORUN = 'ignoreAutoRun'
DEBUG = 'debug'

SCRAPPERS: Dict[str, Dict[str, Any]] = {
    'Infojobs': {  # first to solve security filter
        TIMER: getSeconds(getEnv('INFOJOBS_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('INFOJOBS_IGNORE_AUTORUN', False),
        DEBUG: False
    },
    'Tecnoempleo': {  # first to solve security filter
        TIMER: getSeconds(getEnv('TECNOEMPLEO_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('TECNOEMPLEO_IGNORE_AUTORUN', False),
        DEBUG: False
    },
    'Linkedin': {
        TIMER: getSeconds(getEnv('LINKEDIN_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('LINKEDIN_IGNORE_AUTORUN', False),
        CLOSE_TAB: True,
        DEBUG: False,
    },
    'Glassdoor': {
        TIMER: getSeconds(getEnv('GLASSDOOR_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('GLASSDOOR_IGNORE_AUTORUN', False),
        DEBUG: False,
    },
    'Indeed': {
        TIMER: getSeconds(getEnv('INDEED_RUN_CADENCY')),
        IGNORE_AUTORUN: getEnvBool('INDEED_IGNORE_AUTORUN', False),
        DEBUG: False,
    },
}

RUN_IN_TABS = getEnvBool('RUN_IN_TABS', False)
NEXT_SCRAP_TIMER = '10m'
MAX_NAME = max([len(k) for k in SCRAPPERS.keys()]) if SCRAPPERS else 0
