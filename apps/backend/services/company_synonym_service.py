from typing import List, Dict, Any, Optional
from repositories.company_synonym_repository import CompanySynonymRepository


class CompanySynonymService:
    def __init__(self):
        self.repo = CompanySynonymRepository()

    def list_groups(self) -> List[Dict[str, Any]]:
        return self.repo.list_groups()

    def get_synonyms(self, name: str) -> List[str]:
        return self.repo.find_synonyms(name)

    def create_group(self, names: List[str]) -> Optional[int]:
        if len(names) < 2:
            return None
        return self.repo.create_group(names)

    def add_to_group(self, group_id: int, name: str) -> bool:
        return self.repo.add_to_group(group_id, name)

    def remove_name(self, name: str) -> bool:
        return self.repo.remove_name(name)
