from typing import Any, Dict
from commonlib.util import getEnv, getEnvBool, getSeconds

DEBUG = getEnvBool('SCRAPPER_DEBUG', False)
TIMER = 'timer'
NEW_ARCH = 'newArchitecture'
CLOSE_TAB = 'closeTab'
IGNORE_AUTORUN = 'ignoreAutoRun'

SCRAPPERS: Dict[str, Dict[str, Any]] = {
    'Infojobs': {  # first to solve security filter
        TIMER: getSeconds(getEnv('INFOJOBS_RUN_CADENCY'))
    },
    'Tecnoempleo': {  # first to solve security filter
        TIMER: getSeconds(getEnv('TECNOEMPLEO_RUN_CADENCY'))
    },
    'Linkedin': {
        TIMER: getSeconds(getEnv('LINKEDIN_RUN_CADENCY')),
        NEW_ARCH: getEnvBool('LINKEDIN_NEW_ARCHITECTURE', False),
        CLOSE_TAB: True,
    },
    'Glassdoor': {
        TIMER: getSeconds(getEnv('GLASSDOOR_RUN_CADENCY'))
    },
    'Indeed': {
        TIMER: getSeconds(getEnv('INDEED_RUN_CADENCY')),
        IGNORE_AUTORUN: True
    },
}

RUN_IN_TABS = getEnvBool('RUN_IN_TABS', False)
NEXT_SCRAP_TIMER = '10m'
MAX_NAME = max([len(k) for k in SCRAPPERS.keys()]) if SCRAPPERS else 0
