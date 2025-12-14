from typing import Any, Optional

from commonlib.util import getDatetimeNow, getTimeUnits, consoleTimer
from commonlib.terminalColor import cyan, red, yellow
from scrapper.scrapper_config import (
    SCRAPPERS, TIMER, IGNORE_AUTORUN, NEXT_SCRAP_TIMER,
    MAX_NAME, RUN_IN_TABS
)
from scrapper.persistence_manager import PersistenceManager
from scrapper.seleniumUtil import SeleniumUtil
from scrapper.container.scrapper_container import ScrapperContainer
from scrapper.scrapper_execution import executeScrapper, executeScrapperPreload, runPreload

def getProperties(name: str) -> Optional[dict[str, Any]]:
    return SCRAPPERS.get(name.capitalize())

def validScrapperName(name: str):
    if getProperties(name) is not None:
        return True
    print(red(f"Invalid scrapper web page name {name}"))
    print(yellow(f"Available web page scrapper names: {SCRAPPERS.keys()}"))
    return False

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

def runAllScrappers(waitBeforeFirstRuns, starting, startingAt, persistenceManager: PersistenceManager, seleniumUtil: SeleniumUtil, scrapperContainer: ScrapperContainer, loops=99999999999):
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
                if not executeScrapperPreload(runThis['name'], runThis['properties'], seleniumUtil, scrapperContainer, persistenceManager):
                    return
            if not executeScrapper(runThis['name'], runThis['properties'], persistenceManager, seleniumUtil, scrapperContainer):
                return
        waitBeforeFirstRuns = False
        consoleTimer("Waiting for next scrapping execution trigger, ", NEXT_SCRAP_TIMER)

def runSpecifiedScrappers(scrappersList: list, persistenceManager: PersistenceManager, seleniumUtil: SeleniumUtil, scrapperContainer: ScrapperContainer):
    print(f'Executing specified scrappers: {scrappersList}')
    for arg in scrappersList:
        if validScrapperName(arg):
            properties = SCRAPPERS[arg.capitalize()]
            if runPreload(properties):
                if not executeScrapperPreload(arg.capitalize(), properties, seleniumUtil, scrapperContainer, persistenceManager):
                    return
            if not executeScrapper(arg.capitalize(), properties, persistenceManager, seleniumUtil, scrapperContainer):
                return
