import time
from typing import Any, Optional

from commonlib.util import getEnv, getDatetimeNow
from commonlib.terminalColor import cyan, red, yellow, green
from commonlib.keep_system_awake import KeepSystemAwake
from scrapper.core import baseScrapper
from scrapper import tecnoempleo, infojobs, linkedin, glassdoor, indeed
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.core.scrapper_config import (
    CLOSE_TAB, RUN_IN_TABS, DEBUG, SCRAPPERS
)

def abortExecution() -> bool:
    print(yellow("Scraper interrupted. Waiting 3 seconds... (Ctrl+C to stop all)"))
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print(red("Stopping all scrappers..."))
        return True
    return False

def runPreload(properties: dict) -> bool:
    return not properties.get('preloaded', False) or properties.get(CLOSE_TAB, False) or not RUN_IN_TABS

def runScrapper(name: str, preloadOnly: bool, persistenceManager: PersistenceManager, seleniumUtil: SeleniumService):
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

def executeScrapperPreload(name: str, properties: dict, seleniumUtil: SeleniumService, persistenceManager: PersistenceManager) -> bool:
    """ returns True if KeyboardInterrupt """
    try:
        with KeepSystemAwake():
            if RUN_IN_TABS:
                seleniumUtil.tab(name)
            runScrapper(name, True, persistenceManager, seleniumUtil)
        properties['preloaded'] = True
    except Exception:
        baseScrapper.debug(DEBUG, f"Error occurred while preloading {name}:", True)
        properties['preloaded'] = False
    except KeyboardInterrupt:
        persistenceManager.update_last_execution(name, None)
        if abortExecution():
            return False
    return True

def executeScrapper(name: str, properties: dict, persistenceManager: PersistenceManager, seleniumUtil: SeleniumService) -> bool:
    """ returns False if double KeyboardInterrupt """
    try:
        with KeepSystemAwake():
            runScrapper(name, False, persistenceManager, seleniumUtil)
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

def runScrapperPageUrl(url: str):
    for name, properties in SCRAPPERS.items():
        if url.find(name.lower()) != -1:
            print(cyan(f'Running scrapper for pageUrl: {url}'))
            match name.lower():
                case 'linkedin':
                    linkedin.processUrl(url)
                case _:
                    raise Exception(f"Invalid scrapper web page name {name}, only linkedin is implemented")
