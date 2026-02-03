import json
import os
from typing import List, Dict, Any
from repositories.filter_configurations_repository import FilterConfigurationsRepository

class FilterConfigurationsService:
    def __init__(self, repo: FilterConfigurationsRepository = None):
        self.repo = repo or FilterConfigurationsRepository()
    
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
    
    def create(self, name: str, filters: dict, notify: bool = False, statistics: bool = True) -> Dict[str, Any]:
        existing = self.repo.find_by_name(name)
        if existing:
            raise ValueError(f"Configuration with name '{name}' already exists")
        config_id = self.repo.create(name, filters, notify, statistics)
        return self.repo.find_by_id(config_id)
    
    def update(self, config_id: int, name: str = None, filters: dict = None, notify: bool = None, statistics: bool = None) -> Dict[str, Any]:
        existing = self.repo.find_by_id(config_id)
        if not existing:
            raise ValueError(f"Configuration with id {config_id} not found")
        if name is not None and name != existing['name']:
            name_exists = self.repo.find_by_name(name)
            if name_exists:
                raise ValueError(f"Configuration with name '{name}' already exists")
        self.repo.update(config_id, name, filters, notify, statistics)
        return self.repo.find_by_id(config_id)
    
    def delete(self, config_id: int) -> bool:
        existing = self.repo.find_by_id(config_id)
        if not existing:
            raise ValueError(f"Configuration with id {config_id} not found")
        return self.repo.delete(config_id)
    
    def seed_defaults(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, '..', 'resources', 'defaultFilterConfigurations.json')
        if not os.path.exists(json_path):
            return
        with open(json_path, 'r', encoding='utf-8') as f:
            defaults = json.load(f)
        for config in defaults:
            name = config.get('name')
            filters = config.get('filters', {})
            notify = config.get('notify', False)
            existing = self.repo.find_by_name(name)
            if not existing:
                self.repo.create(name, filters, notify)
