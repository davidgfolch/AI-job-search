from abc import ABC, abstractmethod
from typing import Tuple
from commonlib.terminalColor import yellow
from ..services.selenium.seleniumService import SeleniumService

class BaseNavigator(ABC):
    def __init__(self, selenium: SeleniumService):
        self.selenium = selenium

    def wait_until_page_is_loaded(self):
        self.selenium.waitUntilPageIsLoaded()

    def go_back(self):
        self.selenium.back()

    def load_page(self, url: str):
        print(yellow(f'Loading page {url}'))
        self.selenium.loadPage(url)
        self.selenium.waitUntilPageIsLoaded()

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
