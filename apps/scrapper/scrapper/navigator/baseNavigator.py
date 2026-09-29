from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional
from urllib.parse import urlsplit
from commonlib.observability import get_logger
from ..services.selenium.browser_service import sleep
from ..core.utils import pageExists
from ..services.selenium.seleniumService import SeleniumService
from ..services.scrapling.scraplingService import ScraplingService

logger = get_logger("scrapper.baseNavigator")

class BaseNavigator(ABC):
    def __init__(self, browser_service: SeleniumService | ScraplingService, debug: bool):
        self.selenium = browser_service
        self.debug = debug
        self.current_page: Optional[Any] = None

    def wait_until_page_is_loaded(self):
        self.selenium.waitUntilPageIsLoaded()

    def go_back(self):
        self.selenium.back()

    def load_page(self, url: str):
        parsed = urlsplit(url)
        logger.debug("page.loading", url_host=parsed.netloc, url_path=parsed.path)
        self.selenium.loadPage(url)
        self.selenium.waitUntilPageIsLoaded()

    def fast_forward_page(self, start_page: int, total_results: int, jobs_x_page: int) -> int:
        """
        Fast forwards to the start_page by clicking next page button.
        Returns the page number reached (usually start_page).
        """
        page = 1
        if start_page > 1 and pageExists(start_page, total_results, jobs_x_page):
            logger.debug("page.fast_forwarding", start_page=start_page, total_results=total_results, jobs_x_page=jobs_x_page)
            while page < start_page:
                if self.click_next_page():
                    page += 1
                    self.wait_until_page_is_loaded()
                    sleep(2, 2)
                else:
                    break
        return page

    @abstractmethod
    def get_total_results(self, *args, **kwargs) -> int:
        pass

    @abstractmethod
    def click_next_page(self) -> bool:
        pass

    @abstractmethod
    def scroll_jobs_list(self, idx: int):
        pass

    @abstractmethod
    def get_job_data(self) -> Tuple[str, ...]:
        pass

    def get_url(self) -> str:
        if hasattr(self.selenium, 'getUrl'):
            return self.selenium.getUrl()
        return ""

    def close(self):
        if hasattr(self.selenium, 'close'):
            self.selenium.close()
