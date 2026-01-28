from typing import List, Optional, Dict, Any
import re
from repositories.skills_repository import SkillsRepository
from models.skill import Skill

class SkillsService:
    def __init__(self):
        self.repository = SkillsRepository()

    def _normalize_skill_name(self, name: str) -> str:
        cleaned = re.sub(r'[^a-zA-Z0-9\s\+\.#]', ' ', name)
        normalized = re.sub(r'\s+', ' ', cleaned).strip()
        return normalized.title()

    def _find_skill_by_name(self, name: str) -> tuple[str, Optional[Dict[str, Any]]]:
        normalized_name = self._normalize_skill_name(name)
        return normalized_name, self.repository.find_by_name_case_insensitive(normalized_name)

    def list_skills(self) -> List[Skill]:
        return self.repository.list_skills()

    def create_skill(self, skill: Skill) -> str:
        normalized_name, existing = self._find_skill_by_name(skill.name)
        if existing:
            return existing['name']
        skill.name = normalized_name
        return self.repository.create_skill(skill)

    def update_skill(self, name: str, update_data: Dict[str, Any]) -> Optional[str]:
        _, existing = self._find_skill_by_name(name)
        if not existing:
            return None
        return self.repository.update_skill(existing['name'], update_data)

    def delete_skill(self, name: str) -> bool:
        _, existing = self._find_skill_by_name(name)
        if not existing:
            return False
        return self.repository.delete_skill(existing['name'])

    def bulk_create_skills(self, skills: List[Skill]) -> int:
        count = 0
        for skill in skills:
            try:
                # Basic upsert logic: try create, if fails (duplicate), could update but we will just try create for migration
                # Actually, for "manual import" we want to overwrite or merge. 
                # Let's assume we maintain existing logic: if exists, we might skipping or updating.
                # For simplicity, let's just try to create and ignore errors or handle simple updates if needed.
                existing = self.repository.update_skill(skill.name, {
                    "description": skill.description,
                    "learning_path": skill.learning_path,
                    "disabled": skill.disabled
                })
                if not existing:
                    self.repository.create_skill(skill)
                count += 1
            except Exception as e:
                print(f"Error saving skill {skill.name}: {e}")
        return count
