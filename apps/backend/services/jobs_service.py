from typing import Optional, Dict, Any, List
from repositories.jobs_repository import JobsRepository
from utils.filter_parser import extract_boolean_filters, extract_filter_params, BOOLEAN_FILTER_KEYS
from utils.job_utils import search_partial_company


class JobsService:
    def __init__(self):
        self.repo = JobsRepository()

    def list_jobs(self, page: int, size: int, search: Optional[str] = None,
                  status: Optional[str] = None, not_status: Optional[str] = None,
                  days_old: Optional[int] = None, salary: Optional[str] = None,
                  order: Optional[str] = "created desc",
                  boolean_filters: Optional[Dict[str, Optional[bool]]] = None,
                  sql_filter: Optional[str] = None,
                  ids: Optional[List[int]] = None,
                  created_after: Optional[str] = None) -> Dict[str, Any]:
        return self.repo.list_jobs(
            page=page, size=size, search=search, status=status, not_status=not_status,
            days_old=days_old, salary=salary, order=order, boolean_filters=boolean_filters,
            sql_filter=sql_filter, ids=ids, created_after=created_after)

    def count_jobs(self, search: Optional[str] = None, status: Optional[str] = None,
                   not_status: Optional[str] = None, days_old: Optional[int] = None,
                   salary: Optional[str] = None,
                   boolean_filters: Optional[Dict[str, Optional[bool]]] = None,
                   sql_filter: Optional[str] = None, ids: Optional[List[int]] = None,
                   created_after: Optional[str] = None) -> int:
        return self.repo.count_jobs(
            search=search, status=status, not_status=not_status, days_old=days_old,
            salary=salary, boolean_filters=boolean_filters, sql_filter=sql_filter,
            ids=ids, created_after=created_after)

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.repo.get_db() as db:
            row = self.repo.fetch_job_row(db, job_id)
            if not row:
                return None
            columns = self.repo.fetch_columns(db)
            return {col: val for col, val in zip(columns, row)}

    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = self.repo.update_job(job_id, update_data)
        return self.get_job(job_id) if result else None

    def create_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if 'job_id' not in job_data:
            job_data['job_id'] = f'manual-{int(__import__("time").time() * 1000)}'
        job_id = self.repo.create_job(job_data)
        return self.get_job(job_id) if job_id else None

    def get_applied_jobs_by_company_name(self, company: str,
                                         client: Optional[str] = None) -> List[Dict[str, Any]]:
        if not company or not company.strip():
            raise ValueError("Company name must be a non-empty string")
        company_raw = company.lower().replace("'", "''")
        rows = self.repo.find_applied_by_company(client, client) if company_raw == 'joppy' and client \
            else self.repo.find_applied_by_company(company_raw)
        if not rows:
            regex = search_partial_company(company_raw)
            if regex:
                try:
                    rows = self.repo.find_applied_jobs_by_regex(regex)
                except Exception:
                    rows = []
        return [{'id': row[0], 'created': row[1].isoformat() if row[1] else None} for row in rows]

    def bulk_update_jobs(self, update_data: Dict[str, Any], ids: Optional[List[int]] = None,
                         filters: Optional[Dict[str, Any]] = None, select_all: bool = False) -> int:
        if select_all and filters:
            params = extract_filter_params(filters)
            where, db_params = self.repo.build_where(**params)
            return self.repo.update_jobs_by_filter(where, db_params, update_data)
        elif ids:
            return self.repo.update_jobs_by_ids(ids, update_data)
        return 0

    def delete_jobs(self, ids: Optional[List[int]] = None, filters: Optional[Dict[str, Any]] = None,
                    select_all: bool = False) -> int:
        if select_all and filters:
            params = extract_filter_params(filters)
            where, db_params = self.repo.build_where(**params)
            return self.repo.delete_jobs_by_filter(where, db_params)
        elif ids:
            return self.repo.delete_jobs_by_ids(ids)
        return 0
