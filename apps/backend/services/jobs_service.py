from typing import Optional, Dict, Any, List
from repositories.jobs_repository import JobsRepository
from repositories.jobDeleteRepository import JobDeleteRepository
from repositories.jobQueryRepository import JobQueryRepository
from repositories.queries.jobs_query_builder import build_jobs_where_clause
from services.jobQueryService import JobQueryService
from services.jobSnapshotService import JobSnapshotService
from commonlib.jobSnapshotRepository import JobSnapshotRepository
from utils.filter_parser import extract_filter_params


class JobsService:
    def __init__(self):
        self.repo = JobsRepository()
        self.delete_repo = JobDeleteRepository()
        self.query_service = JobQueryService()
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
        )

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.repo.get_db() as db:
            row = self.repo.fetch_job_row(db, job_id)
            if not row:
                return None
            columns = self.repo.fetch_columns(db)
            return {col: val for col, val in zip(columns, row)}

    def build_where(self, **kwargs):
        return build_jobs_where_clause(**kwargs)

    def update_job(
        self, job_id: int, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        old_job = self.get_job(job_id)
        result = self.repo.update_job(job_id, update_data)
        if result and old_job:
            self._maybe_create_snapshot(old_job, update_data)
        return self.get_job(job_id) if result else None

    def _maybe_create_snapshot(self, old_job: Dict[str, Any], new_data: Dict[str, Any]):
        applied_changed = (
            "applied" in new_data and new_data["applied"] and not old_job.get("applied")
        )
        discarded_changed = (
            "discarded" in new_data
            and new_data["discarded"]
            and not old_job.get("discarded")
        )
        interview_flags = [
            "interview",
            "interview_rh",
            "interview_tech",
            "interview_technical_test",
        ]
        interview_changed = any(
            flag in new_data and new_data[flag] and not old_job.get(flag)
            for flag in interview_flags
        )

        if applied_changed:
            self.snapshot_service.snapshot_on_applied(old_job)
        elif discarded_changed:
            self.snapshot_service.snapshot_on_discarded(old_job)
        elif interview_changed:
            self.snapshot_service.snapshot_on_interview(old_job)

    def create_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "job_id" not in job_data:
            job_data["job_id"] = f"manual-{int(__import__('time').time() * 1000)}"
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
            return self.delete_repo.update_jobs_by_filter(where, db_params, update_data)
        elif ids:
            return self.delete_repo.update_jobs_by_ids(ids, update_data)
        return 0

    def _build_snapshot_queries(self, jobs: List[Dict[str, Any]]) -> List[tuple]:
        snapshot_queries = []
        for job in jobs:
            query, snapshot_params = (
                JobSnapshotRepository.build_snapshot_query_and_params(job, "DELETED")
            )
            snapshot_queries.append((query, snapshot_params))
        return snapshot_queries

    def _delete_by_filters(self, filters: Dict[str, Any]) -> int:
        params = extract_filter_params(filters)
        where, db_params = build_jobs_where_clause(**params)
        jobs_to_delete = self.delete_repo.get_jobs_by_filter(where, db_params)
        snapshot_queries = self._build_snapshot_queries(jobs_to_delete)
        return self.delete_repo.delete_jobs_with_snapshots(
            where, db_params, snapshot_queries
        )

    def _delete_by_ids(self, ids: List[int]) -> int:
        snapshot_queries = []
        for job_id in ids:
            job = self.get_job(job_id)
            if job:
                query, snapshot_params = (
                    JobSnapshotRepository.build_snapshot_query_and_params(
                        job, "DELETED"
                    )
                )
                snapshot_queries.append((query, snapshot_params))
        return self.delete_repo.delete_jobs_with_snapshots(
            ["id IN (" + ", ".join(["%s"] * len(ids)) + ")"], ids, snapshot_queries
        )

    def delete_jobs(
        self,
        ids: Optional[List[int]] = None,
        filters: Optional[Dict[str, Any]] = None,
        select_all: bool = False,
    ) -> int:
        if select_all and filters:
            return self._delete_by_filters(filters)
        elif ids:
            return self._delete_by_ids(ids)
        return 0
