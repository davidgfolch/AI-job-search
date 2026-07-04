import json
import os
from typing import Dict, Any, Optional
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.sql.scrapper_state_repository import ScrapperStateRepository

class PersistenceManager:
    def __init__(self, repository: Optional[ScrapperStateRepository] = None):
        self._repository = repository
        self.state = self.load()

    def load(self) -> Dict[str, Any]:
        try:
            return self._repository.get_all()
        except Exception:
            return {}

    def save(self):
        for site, site_state in self.state.items():
            self._repository.upsert(site, site_state)
        return

    def get_state(self, site: str) -> Dict[str, Any]:
        return self.state.get(site, {})

    def update_state(self, site: str, keyword: str, page: int):
        if site not in self.state:
            self.state[site] = {}
        self.state[site]['keyword'] = keyword
        self.state[site]['page'] = page
        self.save()

    def clear_state(self, site: str):
        if site in self.state:
            # Keep last_execution and failed keywords if any, remove iteration state
            if 'keyword' in self.state[site]:
                del self.state[site]['keyword']
            if 'page' in self.state[site]:
                del self.state[site]['page']
            self.save()

    def get_last_execution(self, site: str) -> str | None:
        return self.state.get(site, {}).get('last_execution')

    def update_last_execution(self, site: str, timestamp: str | None) -> str | None:
        if site not in self.state:
            self.state[site] = {}
        self.state[site]['last_execution'] = timestamp
        self.save()
        return timestamp

    def get_failed_keywords(self, site: str) -> list[str]:
        return self.state.get(site, {}).get('failed_keywords', [])

    def add_failed_keyword(self, site: str, keyword: str):
        if site not in self.state:
            self.state[site] = {}
        failed = self.state[site].get('failed_keywords', [])
        if keyword not in failed:
            failed.append(keyword)
            self.state[site]['failed_keywords'] = failed
            self.save()
    
    def remove_failed_keyword(self, site: str, keyword: str):
        if site in self.state:
            failed = self.state[site].get('failed_keywords', [])
            if keyword in failed:
                failed.remove(keyword)
                self.state[site]['failed_keywords'] = failed
                self.save()

    def prepare_resume(self, site: str):
        state = self.get_state(site)
        self._resume_keyword = state.get('keyword')
        self._resume_page = state.get('page', 1)
        self._is_skipping = bool(self._resume_keyword)

    def should_skip_keyword(self, current_keyword: str) -> tuple[bool, int]:
        """Returns (should_skip, start_page)"""
        start_page = 1
        if hasattr(self, '_resume_keyword') and self._resume_keyword:
            if self._resume_keyword == current_keyword:
                self._is_skipping = False
                start_page = self._resume_page
            elif self._is_skipping:
                return True, 1
        return False, start_page

    def set_error(self, site: str, error: str):
        if site not in self.state:
            self.state[site] = {}
        self.state[site]['last_error'] = error
        self.state[site]['last_error_time'] = getDatetimeNowStr()
        self.save()

    def finalize_scrapper(self, site: str):
        from commonlib.terminalColor import yellow
        if not self.get_failed_keywords(site):
            if 'last_error' in self.state.get(site, {}):
                del self.state[site]['last_error']
                if 'last_error_time' in self.state[site]:
                    del self.state[site]['last_error_time']
            self.clear_state(site)
        else:
            print(yellow(f"Scrapper finished with failed keywords. State preserved for retry."))
        self.save()

