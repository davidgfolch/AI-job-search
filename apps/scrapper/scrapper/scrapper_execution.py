import time
from typing import Any, Optional

from commonlib.util import getEnv, getDatetimeNow
from commonlib.terminalColor import cyan, red, yellow, green
from commonlib.keep_system_awake import KeepSystemAwake
from scrapper import baseScrapper, tecnoempleo, infojobs, linkedin, glassdoor, indeed
from scrapper.persistence_manager import PersistenceManager
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.container.scrapper_container import ScrapperContainer
from scrapper.scrapper_config import (
    NEW_ARCH, CLOSE_TAB, RUN_IN_TABS, DEBUG, SCRAPPERS
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

def hasNewArchitecture(name: str, properties: dict[str, Any], scrapperContainer: ScrapperContainer) -> bool:
    try:
        if not bool(properties.get(NEW_ARCH, False)):
            print(f"⚠️  Using OLD architecture for {name}, new architecture DISABLED")
            return False
        scrapperContainer.get_scrapping_service(name.lower())
        print(cyan(f"Using NEW SOLID architecture for {name}"))
        return True
    except Exception:
        baseScrapper.debug(DEBUG, f"⚠️  Using OLD architecture for {name}, new architecture not available")
        return False

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

def runPreloadNewArchitecture(name: str, scrapperContainer: ScrapperContainer, seleniumUtil: SeleniumService):
    try:
        scrapping_service = scrapperContainer.get_scrapping_service(name.lower())
        results = scrapping_service.executeScrapping(seleniumUtil, [], preloadOnly=True)
        if not results.get('login_success', False):
            print(red(f"Preload failed for {name}"))
    except Exception:
        baseScrapper.debug(DEBUG)

def runScrapperNewArchitecture(name: str, properties: dict, persistenceManager: PersistenceManager, scrapperContainer: ScrapperContainer, seleniumUtil: SeleniumService):
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

def executeScrapperPreload(name: str, properties: dict, seleniumUtil: SeleniumService, scrapperContainer: ScrapperContainer, persistenceManager: PersistenceManager) -> bool:
    """ returns True if KeyboardInterrupt """
    try:
        with KeepSystemAwake():
            if RUN_IN_TABS:
                seleniumUtil.tab(name)
            if hasNewArchitecture(name, properties, scrapperContainer):
                runPreloadNewArchitecture(name, scrapperContainer, seleniumUtil)
            else:
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

def executeScrapper(name: str, properties: dict, persistenceManager: PersistenceManager, seleniumUtil: SeleniumService, scrapperContainer: ScrapperContainer) -> bool:
    """ returns False if double KeyboardInterrupt """
    try:
        with KeepSystemAwake():
            if hasNewArchitecture(name, properties, scrapperContainer):
                runScrapperNewArchitecture(name, properties, persistenceManager, scrapperContainer, seleniumUtil)
            else:
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
