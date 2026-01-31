from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from models.job import AppliedCompanyJob
from services.jobs_service import JobsService

router = APIRouter()

def get_service():
    return JobsService()

@router.get("/applied-by-company", response_model=List[AppliedCompanyJob])
def get_applied_jobs_by_company(
    company: str = Query(..., description="Company name to search for"),
    client: Optional[str] = Query(None, description="Optional client name for Joppy special case"),
    service: JobsService = Depends(get_service)
):
    try:
        results = service.get_applied_jobs_by_company_name(company, client)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [AppliedCompanyJob(**r) for r in results]
