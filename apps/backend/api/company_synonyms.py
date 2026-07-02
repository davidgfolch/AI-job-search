from typing import List
from fastapi import APIRouter, HTTPException, Query
from models.company_synonym import SynonymGroup, SynonymGroupCreate, SynonymAddRequest
from services.company_synonym_service import CompanySynonymService

router = APIRouter()
service = CompanySynonymService()


@router.get("", response_model=List[SynonymGroup])
def list_synonym_groups():
    return service.list_groups()


@router.get("/synonyms", response_model=List[str])
def get_synonyms(company: str = Query(..., description="Company name to find synonyms for")):
    return service.get_synonyms(company)


@router.post("/groups", response_model=dict)
def create_synonym_group(body: SynonymGroupCreate):
    if len(body.names) < 2:
        raise HTTPException(status_code=400, detail="At least two names are required")
    group_id = service.create_group(body.names)
    if group_id is None:
        raise HTTPException(status_code=500, detail="Failed to create group")
    return {"group_id": group_id}


@router.post("/groups/{group_id}", response_model=dict)
def add_to_group(group_id: int, body: SynonymAddRequest):
    success = service.add_to_group(group_id, body.name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add name to group")
    return {"status": "success"}


@router.delete("/names/{name:path}", response_model=dict)
def remove_name(name: str):
    success = service.remove_name(name)
    if not success:
        raise HTTPException(status_code=404, detail="Name not found")
    return {"status": "success"}
