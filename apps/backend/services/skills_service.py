from typing import List, Optional, Dict, Any
from repositories.skills_repository import SkillsRepository
from models.skill import Skill

class SkillsService:
    def __init__(self):
        self.repository = SkillsRepository()

    def list_skills(self) -> List[Skill]:
        return self.repository.list_skills()

    def create_skill(self, skill: Skill) -> str:
        # Check if exists could be done here or in repo, doing blindly in repo for now
        return self.repository.create_skill(skill)

    def update_skill(self, name: str, update_data: Dict[str, Any]) -> Optional[str]:
        return self.repository.update_skill(name, update_data)

    def delete_skill(self, name: str) -> bool:
        return self.repository.delete_skill(name)

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
