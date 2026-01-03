from fastapi import APIRouter
from repositories.ddl_repository import DdlRepository

router = APIRouter()
repo = DdlRepository()

@router.get("/schema")
def get_schema():
    return {
        "tables": repo.get_schema(),
        "keywords": repo.get_keywords()
    }
