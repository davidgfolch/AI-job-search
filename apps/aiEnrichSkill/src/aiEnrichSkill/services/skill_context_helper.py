from ..repositories.skill_repository import SkillRepository


def fetch_skill_context_safe(repository: SkillRepository, skill_name: str) -> str:
    try:
        return repository.fetch_skill_context(skill_name)
    except Exception:
        return ""
