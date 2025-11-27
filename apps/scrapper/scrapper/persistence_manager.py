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
