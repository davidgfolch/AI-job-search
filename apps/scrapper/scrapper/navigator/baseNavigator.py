from abc import ABC, abstractmethod
from typing import Tuple
from commonlib.terminalColor import yellow
from ..services.selenium.browser_service import sleep
from ..core.utils import pageExists
from ..services.selenium.seleniumService import SeleniumService

class BaseNavigator(ABC):
    def __init__(self, selenium: SeleniumService, debug: bool = False):
        self.selenium = selenium
        self.debug = debug

    def wait_until_page_is_loaded(self):
        self.selenium.waitUntilPageIsLoaded()

    def go_back(self):
        self.selenium.back()

    def load_page(self, url: str):
        print(f'Loading page {url}')
        self.selenium.loadPage(url)
        self.selenium.waitUntilPageIsLoaded()

    def fast_forward_page(self, start_page: int, total_results: int, jobs_x_page: int) -> int:
        """
        Fast forwards to the start_page by clicking next page button.
        Returns the page number reached (usually start_page).
        """
        page = 1
        if start_page > 1 and pageExists(start_page, total_results, jobs_x_page):
            print(yellow(f"Fast forwarding to page {start_page}..."))
            while page < start_page:
                if self.click_next_page():
                    page += 1
                    self.wait_until_page_is_loaded()
                    sleep(1, 2)
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
    def get_job_data(self) -> Tuple[str, str, str, str, str]:
        pass

    def get_url(self) -> str:
        return self.selenium.getUrl()
