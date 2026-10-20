from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from models.job import (
    Job,
    JobUpdate,
    JobListResponse,
    AppliedCompanyJob,
    JobCreate,
)
from services.jobs_service import JobsService
from services.watcher_matcher import get_watcher_matcher
from pydantic import BaseModel
from api.jobs_applied import router as jobs_applied_router

router = APIRouter()
router.include_router(jobs_applied_router)


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


def notify_watcher(job_ids: List[int], event_type: str, data: dict = None) -> None:
    """Notify background matcher and SSE subscribers of a job write."""
    matcher = get_watcher_matcher()
    matcher.add_pending_ids(job_ids)
    from api.watcher import broadcast_watcher_event
    broadcast_watcher_event(event_type, data or {})


@router.post("", response_model=Job)
def create_job(job_create: JobCreate, service: JobsService = Depends(get_service)):
    job_data = job_create.model_dump(exclude_unset=True)
    job = service.create_job(job_data)
    if not job:
        raise HTTPException(status_code=500, detail="Failed to create job")
    notify_watcher([job["id"]], "job_created", {"job_id": job["id"]})
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
    duplicated: Optional[bool] = None,
    sql_filter: Optional[str] = None,
    ids: Optional[List[int]] = Query(None),
    created_after: Optional[str] = None,
    modality: Optional[List[str]] = Query(None),
    service: JobsService = Depends(get_service),
):
    boolean_filters = {
        key: value
        for key, value in [
            ("flagged", flagged),
            ("like", like),
            ("ignored", ignored),
            ("seen", seen),
            ("applied", applied),
            ("discarded", discarded),
            ("closed", closed),
            ("interview_rh", interview_rh),
            ("interview", interview),
            ("interview_tech", interview_tech),
            ("interview_technical_test", interview_technical_test),
            ("interview_technical_test_done", interview_technical_test_done),
            ("ai_enriched", ai_enriched),
            ("easy_apply", easy_apply),
            ("duplicated", duplicated),
        ]
        if value is not None
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
        created_after=created_after,
        modality=modality,
    )


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: int, service: JobsService = Depends(get_service)):
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=Job)
def update_job(
    job_id: int, job_update: JobUpdate, service: JobsService = Depends(get_service)
):
    update_data = job_update.model_dump(exclude_unset=True)
    job = service.update_job(job_id, update_data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    notify_watcher([job_id], "job_updated", {"job_id": job_id})
    return job


@router.post("/bulk", response_model=dict)
def bulk_update_jobs(
    bulk_update: BulkJobUpdate, service: JobsService = Depends(get_service)
):
    update_data = bulk_update.update.model_dump(exclude_unset=True)
    count = service.bulk_update_jobs(
        update_data=update_data,
        ids=bulk_update.ids,
        filters=bulk_update.filters,
        select_all=bulk_update.select_all,
    )
    ids = bulk_update.ids or []
    if ids:
        notify_watcher(ids, "jobs_bulk_updated", {"job_ids": ids})
    return {"updated": count}


@router.post("/bulk/delete", response_model=dict)
def bulk_delete_jobs(
    bulk_delete: BulkJobDelete, service: JobsService = Depends(get_service)
):
    count = service.delete_jobs(
        ids=bulk_delete.ids,
        filters=bulk_delete.filters,
        select_all=bulk_delete.select_all,
    )
    ids = bulk_delete.ids or []
    if ids:
        notify_watcher(ids, "jobs_deleted", {"job_ids": ids})
    return {"deleted": count}
