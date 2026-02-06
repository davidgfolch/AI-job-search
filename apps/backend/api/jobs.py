from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from models.job import Job, JobUpdate, JobListResponse, AppliedCompanyJob, JobCreate, WatcherStatsResponse
from services.jobs_service import JobsService
from pydantic import BaseModel


router = APIRouter()

class BulkJobUpdate(BaseModel):
    ids: Optional[List[int]] = None
    filters: Optional[dict] = None
    update: JobUpdate
    select_all: bool = False

class BulkJobDelete(BaseModel):
    ids: Optional[List[int]] = None
    filters: Optional[dict] = None
    select_all: bool = False


def get_service():
    return JobsService()

@router.post("", response_model=Job)
def create_job(job_create: JobCreate, service: JobsService = Depends(get_service)):
    job_data = job_create.model_dump(exclude_unset=True)
    job = service.create_job(job_data)
    if not job:
        raise HTTPException(status_code=500, detail="Failed to create job")
    return job

@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    not_status: Optional[str] = None,
    days_old: Optional[int] = None,
    salary: Optional[str] = None,
    order: Optional[str] = "created desc",
    # Boolean field filters
    flagged: Optional[bool] = None,
    like: Optional[bool] = None,
    ignored: Optional[bool] = None,
    seen: Optional[bool] = None,
    applied: Optional[bool] = None,
    discarded: Optional[bool] = None,
    closed: Optional[bool] = None,
    interview_rh: Optional[bool] = None,
    interview: Optional[bool] = None,
    interview_tech: Optional[bool] = None,
    interview_technical_test: Optional[bool] = None,
    interview_technical_test_done: Optional[bool] = None,
    ai_enriched: Optional[bool] = None,
    easy_apply: Optional[bool] = None,
    sql_filter: Optional[str] = None,
    ids: Optional[List[int]] = Query(None),
    created_after: Optional[str] = None,
    service: JobsService = Depends(get_service)
):
    boolean_filters = {
        key: value for key, value in [
            ('flagged', flagged),
            ('like', like),
            ('ignored', ignored),
            ('seen', seen),
            ('applied', applied),
            ('discarded', discarded),
            ('closed', closed),
            ('interview_rh', interview_rh),
            ('interview', interview),
            ('interview_tech', interview_tech),
            ('interview_technical_test', interview_technical_test),
            ('interview_technical_test_done', interview_technical_test_done),
            ('ai_enriched', ai_enriched),
            ('easy_apply', easy_apply),
        ] if value is not None
    }
    
    return service.list_jobs(
        page=page,
        size=size,
        search=search,
        status=status,
        not_status=not_status,
        days_old=days_old,
        salary=salary,
        order=order,
        boolean_filters=boolean_filters,
        sql_filter=sql_filter,
        ids=ids,
        created_after=created_after
    )



@router.get("/watcher-stats")
def get_watcher_stats(
    request: Request,
    config_ids: str = Query(..., description="Comma-separated list of filter configuration IDs"),
    service: JobsService = Depends(get_service)
):
    ids = [int(id.strip()) for id in config_ids.split(',') if id.strip()]
    cutoff_map = {}
    for config_id in ids:
        param_name = f"from_{config_id}"
        if param_name in request.query_params:
            cutoff_map[config_id] = request.query_params[param_name]
    return service.get_watcher_stats(config_ids=ids, cutoff_map=cutoff_map)


# Import the new router
from api.jobs_applied import router as jobs_applied_router
router.include_router(jobs_applied_router)


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: int, service: JobsService = Depends(get_service)):
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.patch("/{job_id}", response_model=Job)
def update_job(job_id: int, job_update: JobUpdate, service: JobsService = Depends(get_service)):
    update_data = job_update.model_dump(exclude_unset=True)
    job = service.update_job(job_id, update_data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/bulk", response_model=dict)
def bulk_update_jobs(bulk_update: BulkJobUpdate, service: JobsService = Depends(get_service)):
    update_data = bulk_update.update.model_dump(exclude_unset=True)
    count = service.bulk_update_jobs(
        update_data=update_data,
        ids=bulk_update.ids,
        filters=bulk_update.filters,
        select_all=bulk_update.select_all
    )
    return {"updated": count}

@router.post("/bulk/delete", response_model=dict)
def bulk_delete_jobs(bulk_delete: BulkJobDelete, service: JobsService = Depends(get_service)):
    # Using BulkJobDelete which doesn't require 'update' field
    count = service.delete_jobs(
        ids=bulk_delete.ids,
        filters=bulk_delete.filters,
        select_all=bulk_delete.select_all
    )
    return {"deleted": count}
