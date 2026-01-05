import time
from typing import Any, Optional

from commonlib.environmentUtil import getEnv
from commonlib.util import getDatetimeNow, getDatetimeNowStr
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

def runScrapperPageUrl(url: str):
    for name, properties in SCRAPPERS.items():
        if url.find(name.lower()) != -1:
            print(cyan(f'Running scrapper for pageUrl: {url}'))
            match name.lower():
                case 'linkedin':
                    linkedin.processUrl(url)
                case _:
                    raise Exception(f"Invalid scrapper web page name {name}, only linkedin is implemented")

class ScrapperExecution:
    def __init__(self, persistenceManager: PersistenceManager, seleniumUtil: SeleniumService):
        self.persistenceManager = persistenceManager
        self.seleniumUtil = seleniumUtil

    def runScrapper(self, name: str, preloadOnly: bool):
        match name.lower():
            case 'infojobs':
                infojobs.run(self.seleniumUtil, preloadOnly, self.persistenceManager)
            case 'tecnoempleo':
                tecnoempleo.run(self.seleniumUtil, preloadOnly, self.persistenceManager)
            case 'linkedin':
                linkedin.run(self.seleniumUtil, preloadOnly, self.persistenceManager)
            case 'glassdoor':
                glassdoor.run(self.seleniumUtil, preloadOnly, self.persistenceManager)
            case 'indeed':
                indeed.run(self.seleniumUtil, preloadOnly, self.persistenceManager)

    def executeScrapperPreload(self, name: str, properties: dict) -> bool:
        """ returns True if KeyboardInterrupt """
        try:
            with KeepSystemAwake():
                if RUN_IN_TABS:
                    self.seleniumUtil.tab(name)
                self.runScrapper(name, True)
            properties['preloaded'] = True
        except Exception:
            baseScrapper.debug(DEBUG, f"Error occurred while preloading {name}:", True)
            properties['preloaded'] = False
        except KeyboardInterrupt:
            self.persistenceManager.update_last_execution(name, None)
            if abortExecution():
                return False
        return True

    def executeScrapper(self, name: str, properties: dict) -> bool:
        """ returns False if double KeyboardInterrupt """
        try:
            with KeepSystemAwake():
                self.runScrapper(name, False)
            self.persistenceManager.update_last_execution(name, getDatetimeNowStr())
        except Exception:
            baseScrapper.debug(DEBUG, f"Error occurred while executing {name}:", True)
            self.persistenceManager.update_last_execution(name, None)
        except KeyboardInterrupt:
            self.persistenceManager.update_last_execution(name, None)
            if abortExecution():
                return False
        finally:
            if RUN_IN_TABS:
                if properties.get(CLOSE_TAB, False):
                    self.seleniumUtil.tabClose(name)
                self.seleniumUtil.tab()  # switches to default tab
        return True
