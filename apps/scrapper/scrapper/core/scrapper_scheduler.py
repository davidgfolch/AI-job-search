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

    def resolve_timer(self, name: str, default_timer: int) -> tuple[int, str]:
        prefix = f"{name.upper()}_RUN_CADENCY_"
        current_ts = getDatetimeNow()
        current_hour = datetime.fromtimestamp(current_ts).hour
        env_vars = getEnvByPrefix(prefix)
        for suffix, value in env_vars.items():
            parts = suffix.split('-')
            if len(parts) == 2:
                start = int(parts[0])
                end = int(parts[1])
                if start <= end:
                    if start <= current_hour <= end:
                        return getSeconds(value), suffix
                else:
                    raise ValueError(f"Invalid hour range: {suffix}")
            else:
                raise ValueError(f"Invalid hour range: {suffix}")
        return default_timer, "Default"

    def timeExpired(self, name: str, properties: dict, lastExecution: str):
        if lastExecution:
            lapsed = getDatetimeNow() - parseDatetime(lastExecution)
            timeoutSeconds, _ = self.resolve_timer(name, properties[TIMER])
            timeLeft = getTimeUnits(timeoutSeconds - lapsed)
            print(f'Executing {name.rjust(MAX_NAME)} in {timeLeft.rjust(11)}')
            if lapsed + 1 <= timeoutSeconds:
                return False
        return True

    def _calculate_scrapper_state(self, name: str, properties: dict, starting: bool, startingAt: str):
        last_exec_time = self.lastExecution(name, properties)
        seconds_remaining = 0
        timer_details = "Unknown"
        timeoutSeconds = 0
        failed_keywords = self.persistenceManager.get_failed_keywords(name)
        if last_exec_time:
            lapsed = getDatetimeNow() - parseDatetime(last_exec_time)
            if failed_keywords:
                timeoutSeconds = 900 # 15 minutes retry
                timer_details = f"Retry({len(failed_keywords)})"
            else:
                timeoutSeconds, timer_details = self.resolve_timer(name, properties[TIMER])
            seconds_remaining = max(0, timeoutSeconds - lapsed)
        else:
             timeoutSeconds, timer_details = self.resolve_timer(name, properties[TIMER])
        cadency_str = getTimeUnits(timeoutSeconds)
        is_starting_target = starting and startingAt == name.capitalize()
        is_starting_mode = starting
        status_msg = "Pending"
        display_wait = getTimeUnits(seconds_remaining)
        if is_starting_mode:
            if is_starting_target:
                seconds_remaining = 0
                status_msg = "STARTING TARGET"
                display_wait = "NOW"
            else:
                seconds_remaining = 999999999
                status_msg = "Skipped (Start)"
                display_wait = "-"
        elif seconds_remaining == 0:
             status_msg = "Ready"
             display_wait = "NOW"
        return seconds_remaining, status_msg, display_wait, timer_details, cadency_str

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
            seconds, status, next_exec, time_range, cadency = self._calculate_scrapper_state(name, properties, starting, startingAt)
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
