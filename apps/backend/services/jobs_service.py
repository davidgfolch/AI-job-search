import time
from typing import Optional, Dict, Any, List
from repositories.jobs_repository import JobsRepository
from repositories.queries.jobs_query_builder import build_jobs_where_clause
from services.jobQueryService import JobQueryService
from services.company_synonym_service import CompanySynonymService
from services.jobSnapshotService import JobSnapshotService
from services.job_delete_service import JobDeleteService
from utils.filter_parser import extract_filter_params


class JobsService:
    def __init__(self):
        self.repo = JobsRepository()
        self.query_service = JobQueryService()
        self.delete_service = JobDeleteService(get_job_callback=self.get_job)
        self._snapshot_service = None

    @property
    def snapshot_service(self):
        if self._snapshot_service is None:
            self._snapshot_service = JobSnapshotService()
        return self._snapshot_service

    def list_jobs(
        self,
        page: int,
        size: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        not_status: Optional[str] = None,
        days_old: Optional[int] = None,
        salary: Optional[str] = None,
        order: Optional[str] = "created desc",
        boolean_filters: Optional[Dict[str, Optional[bool]]] = None,
        sql_filter: Optional[str] = None,
        ids: Optional[List[int]] = None,
        created_after: Optional[str] = None,
        modality: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return self.repo.list_jobs(
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

    def count_jobs(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        not_status: Optional[str] = None,
        days_old: Optional[int] = None,
        salary: Optional[str] = None,
        boolean_filters: Optional[Dict[str, Optional[bool]]] = None,
        sql_filter: Optional[str] = None,
        ids: Optional[List[int]] = None,
        created_after: Optional[str] = None,
        modality: Optional[List[str]] = None,
    ) -> int:
        return self.repo.count_jobs(
            search=search,
            status=status,
            not_status=not_status,
            days_old=days_old,
            salary=salary,
            boolean_filters=boolean_filters,
            sql_filter=sql_filter,
            ids=ids,
            created_after=created_after,
            modality=modality,
        )

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.repo.get_db() as db:
            row = self.repo.fetch_job_row(db, job_id)
            if not row:
                return None
            columns = self.repo.fetch_columns(db)
            result = {col: val for col, val in zip(columns, row)}
            company = result.get("company")
            if company:
                synonym_service = CompanySynonymService()
                result["synonyms"] = synonym_service.get_synonyms(company) or None
            return result

    def build_where(self, **kwargs):
        return build_jobs_where_clause(**kwargs)

    def update_job(
        self, job_id: int, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        old_job = self.get_job(job_id)
        result = self.repo.update_job(job_id, update_data)
        if result and old_job:
            self.snapshot_service.maybe_create_snapshot_on_update(old_job, update_data)
        return self.get_job(job_id) if result else None

    def create_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "job_id" not in job_data:
            job_data["job_id"] = f"manual-{int(time.time() * 1000)}"
        job_id = self.repo.create_job(job_data)
        return self.get_job(job_id) if job_id else None

    def get_applied_jobs_by_company_name(
        self, company: str, client: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.query_service.get_applied_jobs_by_company_name(company, client)

    def bulk_update_jobs(
        self,
        update_data: Dict[str, Any],
        ids: Optional[List[int]] = None,
        filters: Optional[Dict[str, Any]] = None,
        select_all: bool = False,
    ) -> int:
        if select_all and filters:
            params = extract_filter_params(filters)
            where, db_params = build_jobs_where_clause(**params)
            return self.delete_service.update_jobs_by_filter(where, db_params, update_data)
        elif ids:
            return self.delete_service.update_jobs_by_ids(ids, update_data)
        return 0

    def delete_jobs(
        self,
        ids: Optional[List[int]] = None,
        filters: Optional[Dict[str, Any]] = None,
        select_all: bool = False,
    ) -> int:
        if select_all and filters:
            return self.delete_service.delete_by_filters(filters)
        elif ids:
            return self.delete_service.delete_by_ids(ids)
        return 0
