from fastapi import APIRouter, Depends, Query

from services.salary_history_service import SalaryHistoryService

router = APIRouter()


def get_service():
    return SalaryHistoryService()


@router.get("/{job_id}/history")
def get_job_history(job_id: int, service: SalaryHistoryService = Depends(get_service)):
    return service.get_job_history(job_id)


@router.get("/history/by-company")
def get_company_history(company: str = Query(...), service: SalaryHistoryService = Depends(get_service)):
    return service.get_company_history(company)
