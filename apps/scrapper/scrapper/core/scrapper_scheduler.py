from typing import Optional

from commonlib.terminalUtil import consoleTimer
from commonlib.observability import get_logger
from commonlib.terminalColor import red, yellow
from commonlib.fileSystemUtil import getSrcPath
from scrapper.core.scrapper_config import (SCRAPPERS, TIMER, AUTORUN, BROWSER, get_debug)
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.core.utils import runPreload
from scrapper.executor.executor_factory import create_executor
from scrapper.core.scrapper_state_calculator import ScrapperStateCalculator
from scrapper.util.terminalTableUtil import print_failed_info_table

logger = get_logger("scrapper.scrapper_scheduler")

class ScrapperScheduler:
    
    def __init__(self, persistenceManager: PersistenceManager):
        self.persistenceManager = persistenceManager

    def getProperties(self, name: str) -> Optional[dict]:
        return SCRAPPERS.get(name.capitalize())

    def validScrapperName(self, name: str):
        if self.getProperties(name) is not None:
            return True
        logger.error("scheduler.invalid_scrapper", scrapper=name, console=red(f"Invalid scrapper web page name {name}"))
        logger.info("scheduler.available_scrappers", scrappers=list(SCRAPPERS.keys()),
                    console=yellow(f"Available web page scrapper names: {SCRAPPERS.keys()}"))
        return False


    def _calculate_and_print_status(self, starting: bool, startingAt: str):
        scrappers_status = []
        # Widths: Scrapper(20) | Status(15) | Next execution(16) | Time range(12) | Cadency(10)
        # Total: 20+3+15+3+16+3+12+3+10 = 85 roughly. 
        print("\n" + "="*95)
        print(f"{'Scrapper':<20} | {'Status':<15} | {'Next execution':<16} | {'Time range':<12} | {'Cadency':<10}")
        print("-" * 95)
        runnable_wait_times = []
        for name, properties in SCRAPPERS.items():
            if not properties.get(AUTORUN):
                continue
            calculator = ScrapperStateCalculator(name, properties, self.persistenceManager)
            seconds, status, next_exec, time_range, cadency = calculator.calculate(starting, startingAt)
            logger.debug("scheduler.scrapper_status", scrapper=name, status=status, next_execution=next_exec, time_range=time_range, cadency=cadency, seconds_remaining=seconds)
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
        executed_startingAt = False
        for scrapper in scrappers_status:
            if scrapper['seconds_remaining'] <= 0:
                name = scrapper['name']
                properties = scrapper['properties']
                debug = get_debug(name)
                browser = properties.get(BROWSER, 'chrome')
                logger.info("scraper.starting", scrapper=name, debug=debug, browser=browser,
                            console=f'{name} DEBUG: {debug}, BROWSER: {browser}')
                with SeleniumService(debug=debug, browser=browser) as seleniumUtil:
                    seleniumUtil.loadPage(f"file://{getSrcPath()}/scrapper/index.html")
                    executor = create_executor(name, seleniumUtil, self.persistenceManager)
                    if runPreload(properties):
                        if not executor.execute_preload(properties):
                            return False, executed_startingAt
                        if not properties.get('preloaded', True): 
                            logger.error("scheduler.preload_failed_skip", scrapper=name,
                                         console=red(f"Skipping execution for {name} due to preload failure."))
                            if hasattr(executor, 'navigator') and executor.navigator:
                                executor.navigator.close()
                            continue
                    if not executor.execute(properties):
                        return False, executed_startingAt
                    properties['preloaded'] = False
                    if starting and startingAt == name.capitalize():
                        executed_startingAt = True
        return True, executed_startingAt

    def runAllScrappers(self, waitBeforeFirstRuns, starting, startingAt, loops=99999999999):
        logger.info("scheduler.started", scrappers=list(SCRAPPERS.keys()), loops=loops, wait_before_first_runs=bool(waitBeforeFirstRuns),
                    console=f'Executing all scrappers: {list(SCRAPPERS.keys())}')
        if starting:
            logger.info("scheduler.starting_at", scrapper=startingAt, console=f'Starting at : {startingAt}')
        count = 0
        while loops == 99999999999 or count < loops:
            count += 1
            scrappers_status, seconds_to_wait = self._calculate_and_print_status(starting, startingAt)
            if seconds_to_wait > 0:
                consoleTimer("Waiting for next execution slot", f"{int(seconds_to_wait)}s")
            should_continue, executed_startingAt = self._execute_scrappers(scrappers_status, starting, startingAt)
            print_failed_info_table(self.persistenceManager)
            if not should_continue:
                return
            if starting and executed_startingAt:
                starting = False

    def runSpecifiedScrappers(self, scrappersList: list):
        logger.info("scheduler.specified_started", scrappers=scrappersList, console=f'Executing specified scrappers: {scrappersList}')
        for arg in scrappersList:
            if self.validScrapperName(arg):
                properties = SCRAPPERS[arg.capitalize()]
                debug = get_debug(arg)
                browser = properties.get(BROWSER, 'chrome')
                logger.info("scraper.starting", scrapper=arg, debug=debug, browser=browser,
                            console=f'{arg} DEBUG: {debug}, BROWSER: {browser}')
                with SeleniumService(debug=debug, browser=browser) as seleniumUtil:
                    seleniumUtil.loadPage(f"file://{getSrcPath()}/scrapper/index.html")
                    executor = create_executor(arg.capitalize(), seleniumUtil, self.persistenceManager)
                    if runPreload(properties):
                        if not executor.execute_preload(properties):
                            if hasattr(executor, 'navigator') and executor.navigator:
                                executor.navigator.close()
                            return
                    if not executor.execute(properties):
                        return
                    properties['preloaded'] = False
        print_failed_info_table(self.persistenceManager)
