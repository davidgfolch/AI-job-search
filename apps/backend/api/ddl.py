from fastapi import APIRouter, HTTPException
from services.ddl_service import DdlService

router = APIRouter()
service = DdlService()


@router.get("/schema")
def get_schema():
    return {"tables": service.get_schema(), "keywords": service.get_keywords()}


@router.get("/schema/enum-values/{table_name}/{column_name}")
def get_enum_values(table_name: str, column_name: str):
    values = service.get_enum_values(table_name, column_name)
    if values is None:
        raise HTTPException(
            status_code=404, detail=f"ENUM column {table_name}.{column_name} not found"
        )
    return values
