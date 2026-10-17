import json
import os
from typing import List, Dict, Any
from repositories.filter_configurations_repository import FilterConfigurationsRepository
from repositories.watcher_repository import WatcherRepository

class FilterConfigurationsService:
    def __init__(self, repo: FilterConfigurationsRepository = None, watcher_repo: WatcherRepository = None):
        self.repo = repo or FilterConfigurationsRepository()
        self.watcher_repo = watcher_repo or WatcherRepository()
    
    def get_all(self) -> List[Dict[str, Any]]:
        count = self.repo.count()
        if count == 0:
            self.seed_defaults()
        return self.repo.find_all()
    
    def get_by_id(self, config_id: int) -> Dict[str, Any]:
        config = self.repo.find_by_id(config_id)
        if not config:
            raise ValueError(f"Configuration with id {config_id} not found")
        return config
    
    def create(self, name: str, filters: dict, watched: bool = False, statistics: bool = True, pinned: bool = False, ordering: int = 0) -> Dict[str, Any]:
        existing = self.repo.find_by_name(name)
        if existing:
            raise ValueError(f"Configuration with name '{name}' already exists")
        config_id = self.repo.create(name, filters, watched, statistics, pinned, ordering)
        return self.repo.find_by_id(config_id)
    
    def update(self, config_id: int, name: str = None, filters: dict = None, watched: bool = None, statistics: bool = None, pinned: bool = None, ordering: int = None) -> Dict[str, Any]:
        existing = self.repo.find_by_id(config_id)
        if not existing:
            raise ValueError(f"Configuration with id {config_id} not found")
        if name is not None and name != existing['name']:
            name_exists = self.repo.find_by_name(name)
            if name_exists:
                raise ValueError(f"Configuration with name '{name}' already exists")
        filters_changed = filters is not None
        self.repo.update(config_id, name, filters, watched, statistics, pinned, ordering)
        if filters_changed and self.watcher_repo is not None:
            self.watcher_repo.invalidate_view(config_id)
        return self.repo.find_by_id(config_id)
    
    def delete(self, config_id: int) -> bool:
        existing = self.repo.find_by_id(config_id)
        if not existing:
            raise ValueError(f"Configuration with id {config_id} not found")
        result = self.repo.delete(config_id)
        if self.watcher_repo is not None:
            self.watcher_repo.invalidate_view(config_id)
        return result
    
    def seed_defaults(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, '..', 'resources', 'defaultFilterConfigurations.json')
        if not os.path.exists(json_path):
            return
        with open(json_path, 'r', encoding='utf-8') as f:
            defaults = json.load(f)
        for i, config in enumerate(defaults):
            name = config.get('name')
            filters = config.get('filters', {})
            watched = config.get('watched', False)
            existing = self.repo.find_by_name(name)
            if not existing:
                self.repo.create(name, filters, watched, ordering=i)
