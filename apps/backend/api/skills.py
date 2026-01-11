from typing import List, Optional
from fastapi import APIRouter, HTTPException
from models.skill import Skill, SkillCreate, SkillUpdate
from services.skills_service import SkillsService

router = APIRouter()
service = SkillsService()

@router.get("", response_model=List[Skill])
def list_skills():
    return service.list_skills()

@router.post("", response_model=int)
def bulk_create_skills(skills: List[Skill]):
    return service.bulk_create_skills(skills)

@router.post("/{name}", response_model=str)
def create_skill(name: str, skill: SkillCreate):
    if name != skill.name:
        raise HTTPException(status_code=400, detail="Name mismatch")
    return service.create_skill(skill)

@router.put("/{name}", response_model=str)
def update_skill(name: str, skill_update: SkillUpdate):
    updated = service.update_skill(name, skill_update.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Skill not found")
    return updated

@router.delete("/{name}")
def delete_skill(name: str):
    success = service.delete_skill(name)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "success"}
