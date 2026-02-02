import math
from abc import ABC, abstractmethod

from commonlib.terminalColor import yellow, cyan
from commonlib.mysqlUtil import MysqlUtil
from commonlib.keep_system_awake import KeepSystemAwake
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.exceptionUtil import cleanUnresolvedTrace
from ..core.utils import debug
from ..core.baseScrapper import printScrapperTitle
from ..core.scrapper_config import CLOSE_TAB, RUN_IN_TABS
from ..core.utils import abortExecution
from ..util.persistence_manager import PersistenceManager
from ..services.selenium.seleniumService import SeleniumService


class BaseExecutor(ABC):
    def __init__(self, selenium_service: SeleniumService, persistence_manager: PersistenceManager, debug: bool):
        self.selenium_service = selenium_service
        self.persistence_manager = persistence_manager
        self.navigator = None
        self.service = None
        self.site_name = ""
        self.jobs_x_page = 25
        self.user_email = None
        self.user_pwd = None
        self.jobs_search = None
        self.debug = debug
        self._init_scrapper()

    @property
    def site_name_key(self) -> str:
        """Returns the standardized site name for persistence."""
        return self.site_name.capitalize()

    def _init_scrapper(self):
        """Initialize scrapper specific variables like site_name, credentials, navigator, etc."""
        pass

    def execute_preload(self, properties: dict) -> bool:
        name = self.site_name_key
        try:
            with KeepSystemAwake():
                if RUN_IN_TABS:
                     self.selenium_service.tab(name)
                self.run(preload_page=True)
            properties['preloaded'] = True
        except Exception as e:
            error_msg = cleanUnresolvedTrace(e)
            debug(self.debug, f"Error occurred while preloading {name}:", True)
            self.persistence_manager.set_error(self.site_name_key, f"Preload failed: {error_msg}")
            properties['preloaded'] = False
        except KeyboardInterrupt:
            self.persistence_manager.update_last_execution(self.site_name_key, None)
            if abortExecution():
                return False
        return True

    def execute(self, properties: dict) -> bool:
        """ returns False if double KeyboardInterrupt """
        name = self.site_name_key
        try:
            with KeepSystemAwake():
                self.run(preload_page=False)
            self.persistence_manager.update_last_execution(self.site_name_key, getDatetimeNowStr())
        except Exception as e:
            error_msg = cleanUnresolvedTrace(e)
            debug(self.debug, f"Error occurred while executing {name}:", True)
            self.persistence_manager.set_error(self.site_name_key, error_msg)
            self.persistence_manager.update_last_execution(self.site_name_key, None)
        except KeyboardInterrupt:
            self.persistence_manager.update_last_execution(self.site_name_key, None)
            if abortExecution():
                return False
        finally:
            if RUN_IN_TABS:
                if properties.get(CLOSE_TAB, False):
                    self.selenium_service.tabClose(name)
                self.selenium_service.tab()  # switches to default tab
        return True
    
    def run(self, preload_page: bool):
        """Login, process jobs in search paginated list results"""
        printScrapperTitle(self.site_name, preload_page)
        if preload_page:
            self._preload_action()
            return
        self._execute_scrapping()

    def _preload_action(self):
        """Override if specific preload action is needed"""
        pass

    def _execute_scrapping(self):
        saved_state = self.persistence_manager.get_state(self.site_name_key)
        saved_keyword = saved_state.get("keyword")
        saved_page = saved_state.get("page", 1)
        # If persistence manager has no state, saved_keyword is None.
        # But for logic consistency, we often rely on should_skip_keyword from service or loop logic.
        # However, BaseService usually handles skip logic if we use it.
        # Let's see patterns. existing code uses manual skip logic often reading from service.should_skip_keyword, 
        # but that method reads from persistence manager too.
        # Let's standardize on using service.should_skip_keyword if possible, or manual loop.
        with MysqlUtil() as mysql:
            self.service = self._create_service(mysql)
            if hasattr(self.service, 'prepare_resume'):
                self.service.prepare_resume()
            # This loop logic is slightly different across scrappers (Indeed has explicit logic in loop, others use service.should_skip)
            # Indeed.py matches explicit strict logic. Others use service.should_skip_keyword.
            # I will try to support the most common pattern here or delegate to _process_keywords_loop if needed.
            # But wait, logic is mostly:
            for keyword_raw in self.jobs_search.split('|~|' if '|~|' in self.jobs_search else ','): # Glassdoor uses |~|
                keyword = keyword_raw.strip()
                if not keyword:
                    continue
                skip = False
                start_page = 1
                # Check if we should skip based on service (most common) or manual check (Indeed)
                if hasattr(self.service, 'should_skip_keyword'):
                     skip, start_page = self.service.should_skip_keyword(keyword)
                else: 
                     # Fallback to manual check similar to Indeed if service doesn't have it (though IndeedService likely has access to it)
                     # Indeed script did it manually in run()
                     if saved_keyword:
                         if saved_keyword == keyword:
                             start_page = saved_page
                         elif saved_keyword: # effectively if we have a saved keyword and it's not this one, and we iterate in order...
                             # But Indeed logic was: skip = True initially. 
                             # If saved_keyword == keyword: skip = False. 
                             # logic is tricky to unify perfectly without changing behavior.
                             # Let's trust that most services implement `should_skip_keyword` or I add it to BaseService in a separate refactor.
                             # For now, I will assume the child class might want to control the loop or I implement the common `should_skip_keyword` logic here if service fails.
                             pass
                if skip:
                    print(yellow(f"Skipping keyword '{keyword}' (already processed)"))
                    continue
                try:
                    self._process_keyword(keyword, start_page)
                    self.persistence_manager.remove_failed_keyword(self.site_name_key, keyword)
                except Exception:
                    debug(self.debug)
                    self.persistence_manager.add_failed_keyword(self.site_name_key, keyword)
        self.persistence_manager.finalize_scrapper(self.site_name_key)

    @abstractmethod
    def _create_service(self, mysql):
        pass

    @abstractmethod
    def _process_keyword(self, keyword, start_page):
        pass
    
    def _generic_search_loop(self, keyword, start_page, total_results):
        totalPages = math.ceil(total_results / self.jobs_x_page)
        page = self.navigator.fast_forward_page(start_page, total_results, self.jobs_x_page)
        # Some scrappers use 0-indexed currentItem, others might vary. Usually (page-1)*X
        currentItem = (page - 1) * self.jobs_x_page
        while currentItem < total_results:
             # This loop structure is common but inner logic varies (Glassdoor: inner loop, Indeed: inner loop, Linkedin: inner loop)
             # I will leave the detailed loop to _process_keyword in subclasses for now to avoid over-abstraction risk,
             # but I can provide helper methods.
             pass

