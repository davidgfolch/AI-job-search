import sys
import time
from typing import Any, Callable, Optional

from commonlib.util import getDatetimeNow, getEnv, getEnvBool, getSeconds, getTimeUnits, getSrcPath, consoleTimer
from commonlib.terminalColor import cyan, red, yellow, green
from scrapper.seleniumUtil import SeleniumUtil
from scrapper import baseScrapper, tecnoempleo, infojobs, linkedin, glassdoor, indeed
from scrapper.persistence_manager import PersistenceManager

from scrapper.container.scrapper_container import ScrapperContainer
from commonlib.keep_system_awake import KeepSystemAwake

DEBUG = getEnvBool('SCRAPPER_DEBUG', False)
TIMER = 'timer'
NEW_ARCH = 'newArchitecture'
CLOSE_TAB = 'closeTab'
IGNORE_AUTORUN = 'ignoreAutoRun'
SCRAP_PAGE_FUNCTION = 'scrapPageFunction'
SCRAPPERS: dict[str, dict[str, Any]] = {
    'Infojobs': {  # first to solve security filter
        TIMER: getSeconds(getEnv('INFOJOBS_RUN_CADENCY'))},
    'Tecnoempleo': {  # first to solve security filter
        TIMER: getSeconds(getEnv('TECNOEMPLEO_RUN_CADENCY'))},
    'Linkedin': {
        TIMER: getSeconds(getEnv('LINKEDIN_RUN_CADENCY')),
        NEW_ARCH: getEnvBool('LINKEDIN_NEW_ARCHITECTURE', False),
        CLOSE_TAB: True,
        SCRAP_PAGE_FUNCTION: linkedin.processUrl},
    'Glassdoor': {
        TIMER: getSeconds(getEnv('GLASSDOOR_RUN_CADENCY'))},
    'Indeed': {
        TIMER: getSeconds(getEnv('INDEED_RUN_CADENCY')),
        IGNORE_AUTORUN: True
    },
}
print(f'Scrappers config: {SCRAPPERS}')
RUN_IN_TABS = getEnvBool('RUN_IN_TABS', False)
NEXT_SCRAP_TIMER = '10m'  # '10m'  # time to wait between scrapping executions
MAX_NAME = max([len(k) for k in SCRAPPERS.keys()])

seleniumUtil: SeleniumUtil = None  # None initialization needed for tests mocks only
persistenceManager: PersistenceManager = None
scrapperContainer: ScrapperContainer = None

def lastExecution(name: str, properties: dict, persistenceManager: PersistenceManager):
    lastExec = persistenceManager.get_last_execution(name)
    if lastExec is None and properties.get('waitBeforeFirstRun'):
        lastExec = persistenceManager.update_last_execution(name, getDatetimeNow())
    return lastExec


def timeExpired(name: str, properties: dict, lastExecution: int):
    if lastExecution:
        lapsed = getDatetimeNow() - lastExecution
        timeoutSeconds = properties[TIMER]
        timeLeft = getTimeUnits(timeoutSeconds - lapsed)
        print(f'Executing {name.rjust(MAX_NAME)} in {timeLeft.rjust(11)}')
        if lapsed + 1 <= timeoutSeconds:
            return False
    return True


def runAllScrappers(waitBeforeFirstRuns, starting, startingAt, loops=99999999999):
    # No arguments specified in command line: run all
    # Specified params: starting glassdoor -> starts with glassdoor
    print(f'Executing all scrappers: {SCRAPPERS.keys()}')
    print(f'Starting at : {startingAt}')
    print(cyan(f'DEBUG: waitBeforeFirstRuns={waitBeforeFirstRuns}, starting={starting}, startingAt={startingAt}'))
    count = 0
    while loops == 99999999999 or count < loops:
        count += 1
        toRun = []
        for name, properties in SCRAPPERS.items():
            properties['waitBeforeFirstRun'] = properties.get('waitBeforeFirstRun', waitBeforeFirstRuns)
            lastExec = lastExecution(name, properties, persistenceManager)
            expired = timeExpired(name, properties, lastExec)
            if expired:
                notStartAtThisOne = (starting and startingAt != name)
                if properties.get(IGNORE_AUTORUN, False) or notStartAtThisOne:
                    print(f'Skipping : {name} (IGNORE_AUTORUN={properties.get(IGNORE_AUTORUN, False)}, notStartAtThisOne={notStartAtThisOne})')
                    continue
                properties['waitBeforeFirstRun'] = False
                toRun.append({"name": name, "properties": properties})
                starting = False
        for runThis in toRun:
            if RUN_IN_TABS:
                seleniumUtil.tab(runThis['name'])
            if runPreload(runThis['properties']):
                if not executeScrapperPreload(runThis['name'], runThis['properties']):
                    return
            if not executeScrapper(runThis['name'], runThis['properties'], persistenceManager):
                return
        waitBeforeFirstRuns = False
        consoleTimer("Waiting for next scrapping execution trigger, ", NEXT_SCRAP_TIMER)




def runSpecifiedScrappers(scrappersList: list):
    print(f'Executing specified scrappers: {scrappersList}')
    for arg in scrappersList:
        if validScrapperName(arg):
            properties = SCRAPPERS[arg.capitalize()]            
            if runPreload(properties):
                if not executeScrapperPreload(arg.capitalize(), properties):
                    return
            if not executeScrapper(arg.capitalize(), properties, persistenceManager):
                return


def runPreload(properties: dict) -> bool:
    return not properties.get('preloaded', False) or properties.get(CLOSE_TAB, False) or not RUN_IN_TABS


def validScrapperName(name: str):
    if getProperties(name) is not None:
        return True
    print(red(f"Invalid scrapper web page name {name}"))
    print(yellow(f"Available web page scrapper names: {SCRAPPERS.keys()}"))
    return False


def getProperties(name: str) -> Optional[dict[str, Any]]:
    return SCRAPPERS.get(name.capitalize())


def hasNewArchitecture(name: str, properties: dict[str, dict[str, Any]]) -> bool:
    try:
        if not bool(properties.get(NEW_ARCH, False)):
            print(f"⚠️  Using OLD architecture for {name}, new architecture DISABLED")
            return False
        scrapperContainer.get_scrapping_service(name.lower())
        print(cyan(f"Using NEW SOLID architecture for {name}"))
        return True
    except Exception:
        print(DEBUG, f"⚠️  Using OLD architecture for {name}, new architecture not available")
        return False


def executeScrapperPreload(name: str, properties: dict) -> bool:
    """ returns True if KeyboardInterrupt """
    try:
        with KeepSystemAwake():
            if RUN_IN_TABS:
                seleniumUtil.tab(name)
            if hasNewArchitecture(name, properties):
                runPreloadNewArchitecture(name)
            else:
                runScrapper(name, True, persistenceManager)
        properties['preloaded'] = True
    except Exception:
        baseScrapper.debug(DEBUG, f"Error occurred while preloading {name}:")
        properties['preloaded'] = False
    except KeyboardInterrupt:
        persistenceManager.update_last_execution(name, None)
        if abortExecution():
            return False
    return True


def runScrapper(name: str, preloadOnly: bool, persistenceManager: PersistenceManager):
    match name.lower():
        case 'infojobs':
            infojobs.run(seleniumUtil, preloadOnly, persistenceManager)
        case 'tecnoempleo':
            tecnoempleo.run(seleniumUtil, preloadOnly, persistenceManager)
        case 'linkedin':
            linkedin.run(seleniumUtil, preloadOnly, persistenceManager)
        case 'glassdoor':
            glassdoor.run(seleniumUtil, preloadOnly, persistenceManager)
        case 'indeed':
            indeed.run(seleniumUtil, preloadOnly, persistenceManager)


def runPreloadNewArchitecture(name: str):
    try:
        scrapping_service = scrapperContainer.get_scrapping_service(name.lower())
        results = scrapping_service.executeScrapping(seleniumUtil, [], preloadOnly=True)
        if not results.get('login_success', False):
            print(red(f"Preload failed for {name}"))
    except Exception:
        baseScrapper.debug(DEBUG)


def executeScrapper(name: str, properties: dict, persistenceManager: PersistenceManager) -> bool:
    """ returns False if double KeyboardInterrupt """
    try:
        with KeepSystemAwake():
            if hasNewArchitecture(name, properties):
                runScrapperNewArchitecture(name, properties, persistenceManager)
            else:
                runScrapper(name, False, persistenceManager)
        persistenceManager.update_last_execution(name, getDatetimeNow())
    except Exception:
        baseScrapper.debug(DEBUG, f"Error occurred while executing {name}:", True)
        persistenceManager.update_last_execution(name, None)
    except KeyboardInterrupt:
        persistenceManager.update_last_execution(name, None)
        if abortExecution():
            return False
    finally:
        if RUN_IN_TABS:
            if properties.get(CLOSE_TAB, False):
                seleniumUtil.tabClose(name)
            seleniumUtil.tab()  # switches to default tab
    return True

def abortExecution() -> bool:
    print(yellow("Scraper interrupted. Waiting 3 seconds... (Ctrl+C to stop all)"))
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print(red("Stopping all scrappers..."))
        return True
    return False


def runScrapperNewArchitecture(name: str, properties: dict, persistenceManager: PersistenceManager):
    try:
        scrapping_service = scrapperContainer.get_scrapping_service(name.lower())
        # FIXME: NEXT LINE SHOULD BE SOMETHING LIKE: baseScrapper.getAndCheckEnvVars(name)
        keywords_list = getEnv('LINKEDIN_JOBS_SEARCH', getEnv('JOBS_SEARCH', '')).split(',')
        results = scrapping_service.executeScrapping(seleniumUtil, keywords_list, preloadOnly=False, persistenceManager=persistenceManager)
        print(green(f"Scrapping completed for {name}:"))
        print(f"  Processed: {results['total_processed']} jobs")
        print(f"  Saved: {results['total_saved']} jobs")
        print(f"  Duplicates: {results['total_duplicates']} jobs")
        if results['errors']:
            print(red(f"  Errors: {len(results['errors'])}"))
            for error in results['errors'][:3]:
                print(red(f"    - {error}"))
    except Exception:
        baseScrapper.debug(DEBUG)


def runScrapperPageUrl(url: str):
    for name, properties in SCRAPPERS.items():
        if url.find(name.lower()) != -1:
            print(cyan(f'Running scrapper for pageUrl: {url}'))
            match name.lower():
                case 'linkedin':
                    linkedin.processUrl(url)
                case _:
                    raise Exception(f"Invalid scrapper web page name {name}, only linkedin is implemented")


def hasArgument(args: list, name: str, info: Callable = (lambda: str)) -> bool:
    exists = name in args
    if exists:
        args.pop(args.index(name))
        print(info())
    return exists


if __name__ == '__main__':
    args = sys.argv
    print(cyan('Scrapper init'))
    print(cyan('Usage: scrapper.py wait starting scrapperName'))
    print(cyan('wait -> waits for scrapper timeout before executing'))
    print(cyan('starting -> starts scrapping at the specified scrapper (by name)'))
    print(cyan('url -> scrapping only the specified url page'))

    wait = hasArgument(args, 'wait', lambda: "'wait' before execution")
    starting = hasArgument(args, 'starting', lambda: f"'starting' at {args[1]} ")
    url = hasArgument(args, 'url', lambda: f"scrapping only url page -> {args[1]} ")

    if len(args) == 2 and url:
        runScrapperPageUrl(args[1])
        exit(0)

    with SeleniumUtil() as seleniumUtil:
        persistenceManager = PersistenceManager()
        scrapperContainer = ScrapperContainer()
        seleniumUtil.loadPage(f"file://{getSrcPath()}/scrapper/index.html")
        if len(args) == 1 or starting or wait:
            startingAt = args[1].capitalize() if starting else None
            runAllScrappers(wait, starting, startingAt)
        else:
            runSpecifiedScrappers(args[1:])
