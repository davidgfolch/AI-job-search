import json
import os
from typing import Dict, Any

class PersistenceManager:
    def __init__(self, filepath: str = 'scrapper_state.json'):
        self.filepath = filepath
        self.state = self.load()

    def load(self) -> Dict[str, Any]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_state(self, site: str) -> Dict[str, Any]:
        return self.state.get(site, {})

    def update_state(self, site: str, keyword: str, page: int):
        self.state[site] = {'keyword': keyword, 'page': page}
        self.save()

    def clear_state(self, site: str):
        if site in self.state:
            del self.state[site]
            self.save()

    def get_last_execution(self, site: str) -> int | None:
        return self.state.get(site, {}).get('last_execution')

    def update_last_execution(self, site: str, timestamp: int) -> int:
        if site not in self.state:
            self.state[site] = {}
        self.state[site]['last_execution'] = timestamp
        self.save()
        return timestamp

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
