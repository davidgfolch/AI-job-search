from typing import Any, Optional

from commonlib.util import consoleTimer
from commonlib.dateUtil import getDatetimeNow, getTimeUnits, getDatetimeNowStr, parseDatetime
from commonlib.terminalColor import cyan, red, yellow
from scrapper.core.scrapper_config import (
    SCRAPPERS, TIMER, IGNORE_AUTORUN, NEXT_SCRAP_TIMER,
    MAX_NAME, RUN_IN_TABS
)
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.core.scrapper_execution import ScrapperExecution, runPreload

class ScrapperScheduler:
    def __init__(self, persistenceManager: PersistenceManager, seleniumUtil: SeleniumService):
        self.persistenceManager = persistenceManager
        self.seleniumUtil = seleniumUtil
        self.scrapperExecution = ScrapperExecution(persistenceManager, seleniumUtil)

    def getProperties(self, name: str) -> Optional[dict[str, Any]]:
        return SCRAPPERS.get(name.capitalize())

    def validScrapperName(self, name: str):
        if self.getProperties(name) is not None:
            return True
        print(red(f"Invalid scrapper web page name {name}"))
        print(yellow(f"Available web page scrapper names: {SCRAPPERS.keys()}"))
        return False

    def lastExecution(self, name: str, properties: dict):
        lastExec = self.persistenceManager.get_last_execution(name)
        if lastExec is None and properties.get('waitBeforeFirstRun'):
            lastExec = self.persistenceManager.update_last_execution(name, getDatetimeNowStr())
        return lastExec

    def timeExpired(self, name: str, properties: dict, lastExecution: str):
        if lastExecution:
            lapsed = getDatetimeNow() - parseDatetime(lastExecution)
            timeoutSeconds = properties[TIMER]
            timeLeft = getTimeUnits(timeoutSeconds - lapsed)
            print(f'Executing {name.rjust(MAX_NAME)} in {timeLeft.rjust(11)}')
            if lapsed + 1 <= timeoutSeconds:
                return False
        return True

    def runAllScrappers(self, waitBeforeFirstRuns, starting, startingAt, loops=99999999999):
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
                lastExec = self.lastExecution(name, properties)
                expired = self.timeExpired(name, properties, lastExec)
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
                    self.seleniumUtil.tab(runThis['name'])
                if runPreload(runThis['properties']):
                    if not self.scrapperExecution.executeScrapperPreload(runThis['name'], runThis['properties']):
                        return
                if not self.scrapperExecution.executeScrapper(runThis['name'], runThis['properties']):
                    return
            waitBeforeFirstRuns = False
            consoleTimer("Waiting for next scrapping execution trigger, ", NEXT_SCRAP_TIMER)

    def runSpecifiedScrappers(self, scrappersList: list):
        print(f'Executing specified scrappers: {scrappersList}')
        for arg in scrappersList:
            if self.validScrapperName(arg):
                properties = SCRAPPERS[arg.capitalize()]
                if runPreload(properties):
                    if not self.scrapperExecution.executeScrapperPreload(arg.capitalize(), properties):
                        return
                if not self.scrapperExecution.executeScrapper(arg.capitalize(), properties):
                    return
