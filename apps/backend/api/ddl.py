from fastapi import APIRouter
from services.ddl_service import DdlService

router = APIRouter()
service = DdlService()

@router.get("/schema")
def get_schema():
    return {
        "tables": service.get_schema(),
        "keywords": service.get_keywords()
    }
