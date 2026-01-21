from typing import Any, Optional
from datetime import datetime

from commonlib.terminalUtil import consoleTimer
from commonlib.dateUtil import getDatetimeNow, getTimeUnits, getDatetimeNowStr, parseDatetime, getSeconds
from commonlib.environmentUtil import getEnvByPrefix
from commonlib.terminalColor import cyan, red, yellow
from scrapper.core.scrapper_config import (SCRAPPERS, TIMER, IGNORE_AUTORUN, NEXT_SCRAP_TIMER, MAX_NAME, RUN_IN_TABS, get_debug)
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.core.utils import runPreload
from scrapper.executor.BaseExecutor import BaseExecutor
from scrapper.core.scrapper_state_calculator import ScrapperStateCalculator

class ScrapperScheduler:
    
    def __init__(self, persistenceManager: PersistenceManager, seleniumUtil: SeleniumService):
        self.persistenceManager = persistenceManager
        self.seleniumUtil = seleniumUtil

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
            calculator = ScrapperStateCalculator(name, properties, self.persistenceManager)
            timeoutSeconds, _ = calculator.resolve_timer(properties[TIMER])
            timeLeft = getTimeUnits(timeoutSeconds - lapsed)
            print(f'Executing {name.rjust(MAX_NAME)} in {timeLeft.rjust(11)}')
            if lapsed + 1 <= timeoutSeconds:
                return False
        return True

    def _calculate_and_print_status(self, starting: bool, startingAt: str):
        scrappers_status = []
        # Widths: Scrapper(20) | Status(15) | Next execution(16) | Time range(12) | Cadency(10)
        # Total: 20+3+15+3+16+3+12+3+10 = 85 roughly. 
        print("\n" + "="*95)
        print(f"{'Scrapper':<20} | {'Status':<15} | {'Next execution':<16} | {'Time range':<12} | {'Cadency':<10}")
        print("-" * 95)
        runnable_wait_times = []
        for name, properties in SCRAPPERS.items():
            if properties.get(IGNORE_AUTORUN, False):
                continue
            calculator = ScrapperStateCalculator(name, properties, self.persistenceManager)
            seconds, status, next_exec, time_range, cadency = calculator.calculate(starting, startingAt)
            print(f"{name:<20} | {status:<15} | {next_exec:<16} | {time_range:<12} | {cadency:<10}")
            is_starting_mode = starting
            is_starting_target = starting and startingAt == name.capitalize()
            if not (is_starting_mode and not is_starting_target):
                runnable_wait_times.append(seconds)
            scrappers_status.append({
                "name": name,
                "properties": properties,
                "seconds_remaining": seconds
            })
        print("="*95 + "\n")
        seconds_to_wait = 0
        if runnable_wait_times:
            seconds_to_wait = min(runnable_wait_times)
        return scrappers_status, seconds_to_wait

    def _execute_scrappers(self, scrappers_status: list, starting: bool, startingAt: str) -> tuple[bool, bool]:
        executed_starting_target = False
        for scrapper in scrappers_status:
            if scrapper['seconds_remaining'] <= 0:
                name = scrapper['name']
                properties = scrapper['properties']
                debug = get_debug(name)
                print(f'{name} DEBUG: {debug}')
                self.seleniumUtil.debug = debug
                if RUN_IN_TABS:
                    self.seleniumUtil.tab(name)
                if runPreload(properties):
                    executor = BaseExecutor.create(name, self.seleniumUtil, self.persistenceManager)
                    if not executor.execute_preload(properties):
                        return False, executed_starting_target
                    if not properties.get('preloaded', True): 
                        print(red(f"Skipping execution for {name} due to preload failure."))
                        continue
                executor = BaseExecutor.create(name, self.seleniumUtil, self.persistenceManager)
                if not executor.execute(properties):
                    return False, executed_starting_target
                if starting and startingAt == name.capitalize():
                    executed_starting_target = True
        return True, executed_starting_target

    def runAllScrappers(self, waitBeforeFirstRuns, starting, startingAt, loops=99999999999):
        print(f'Executing all scrappers: {SCRAPPERS.keys()}')
        if starting:
            print(f'Starting at : {startingAt}')
        count = 0
        while loops == 99999999999 or count < loops:
            count += 1
            scrappers_status, seconds_to_wait = self._calculate_and_print_status(starting, startingAt)
            if seconds_to_wait > 0:
                consoleTimer("Waiting for next execution slot", f"{int(seconds_to_wait)}s")
            should_continue, executed_starting_target = self._execute_scrappers(scrappers_status, starting, startingAt)
            if not should_continue:
                return
            if starting and executed_starting_target:
                starting = False

    def runSpecifiedScrappers(self, scrappersList: list):
        print(f'Executing specified scrappers: {scrappersList}')
        for arg in scrappersList:
            if self.validScrapperName(arg):
                properties = SCRAPPERS[arg.capitalize()]
                if runPreload(properties):
                    executor = BaseExecutor.create(arg.capitalize(), self.seleniumUtil, self.persistenceManager)
                    if not executor.execute_preload(properties):
                        return
                executor = BaseExecutor.create(arg.capitalize(), self.seleniumUtil, self.persistenceManager)
                if not executor.execute(properties):
                    return
