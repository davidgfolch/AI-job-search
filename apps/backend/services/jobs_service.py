from typing import Optional, Dict, Any, List
from repositories.jobs_repository import JobsRepository
from constants import JOB_BOOLEAN_KEYS


class JobsService:
    def __init__(self, repo: JobsRepository = None):
        self.repo = repo or JobsRepository()

    def list_jobs(self, page: int, size: int, search: Optional[str] = None,
                    status: Optional[str] = None, not_status: Optional[str] = None,
                    days_old: Optional[int] = None, salary: Optional[str] = None,
                    order: Optional[str] = "created desc", boolean_filters: Dict[str, Optional[bool]] = None,
                    sql_filter: Optional[str] = None, ids: Optional[List[int]] = None, created_after: Optional[str] = None) -> Dict[str, Any]:
        return self.repo.list_jobs(page, size, search, status, not_status,
            days_old, salary, order, boolean_filters, sql_filter, ids, created_after)

    def count_jobs(self, search: Optional[str] = None,
                    status: Optional[str] = None, not_status: Optional[str] = None,
                    days_old: Optional[int] = None, salary: Optional[str] = None,
                    boolean_filters: Dict[str, Optional[bool]] = None,
                    sql_filter: Optional[str] = None, ids: Optional[List[int]] = None, created_after: Optional[str] = None) -> int:
        return self.repo.count_jobs(search, status, not_status,
            days_old, salary, boolean_filters, sql_filter, ids, created_after)

    def get_watcher_stats(self, config_ids: List[int], watcher_cutoff: Optional[str] = None) -> Dict[int, Dict[str, int]]:
        from services.filter_configurations_service import FilterConfigurationsService
        config_service = FilterConfigurationsService()
        results = {}
        for config_id in config_ids:
            try:
                config = config_service.get_by_id(config_id)
                filters = config['filters']
                search = filters.get('search')
                status = filters.get('status')
                not_status = filters.get('not_status')
                days_old = filters.get('days_old')
                salary = filters.get('salary')
                sql_filter = filters.get('sql_filter')
                created_after = filters.get('created_after')
                boolean_filters = {k: filters.get(k) for k in JOB_BOOLEAN_KEYS if k in filters}
                total = self.count_jobs(search, status, not_status, days_old, salary, boolean_filters, sql_filter, None, created_after)
                new_items = self.count_jobs(search, status, not_status, days_old, salary, boolean_filters, sql_filter, None, created_after=watcher_cutoff)
                results[config_id] = {"total": total, "new_items": new_items}
            except Exception as e:
                print(f"Error getting watcher stats for config {config_id}: {e}")
                results[config_id] = {"total": 0, "new_items": 0}
        return results

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.repo.get_db() as db:
            row = self.repo.fetch_job_row(db, job_id)
            if not row:
                return None
            columns = self.repo.fetch_columns(db)
            return {col: val for col, val in zip(columns, row)}

    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = self.repo.update_job(job_id, update_data)
        if result is None:
            return None
        return self.get_job(job_id)

    def create_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        import time
        # Generate a unique job_id for manual entries
        if 'job_id' not in job_data:
            job_data['job_id'] = f'manual-{int(time.time() * 1000)}'
        job_id = self.repo.create_job(job_data)
        if job_id:
            return self.get_job(job_id)
        return None

    def get_applied_jobs_by_company_name(self, company: str, client: str = None) -> List[Dict[str, Any]]:
        company_raw = company.lower().replace("'", "''") if company else ""
        if company_raw == 'joppy' and client:
            rows = self.repo.find_applied_by_company(client, client)
        else:
            rows = self.repo.find_applied_by_company(company_raw)
        if len(rows) == 0:
            rows = self._search_partial_company(company_raw)
        return [{'id': row[0], 'created': row[1].isoformat() if row[1] else None} for row in rows]

    def _search_partial_company(self, company_raw: str) -> list:
        import re
        company_words = company_raw.split(' ')
        rows = []
        while len(company_words) > 1 and len(rows) == 0:
            company_words = company_words[:-1]
            words = ' '.join(company_words)
            part1 = re.escape(words)
            if len(part1) > 2 and part1 not in ['grupo', 'the', 'inc', 'ltd', 'llc']:
                regex_lookup = f'(^| ){part1}($| )'
                try:
                    rows = self.repo.find_applied_jobs_by_regex(regex_lookup)
                except Exception:
                    pass
        return rows

    def bulk_update_jobs(self, update_data: Dict[str, Any], ids: Optional[List[int]] = None,
                         filters: Optional[Dict[str, Any]] = None, select_all: bool = False) -> int:
        """
        Updates multiple jobs.
        If select_all is True and filters are provided, updates all jobs matching the filters.
        Otherwise, updates the jobs specified in ids.
        """
        if select_all and filters:
            # Extract filter parameters matching list_jobs signature
            page = 1 # Not used for update
            size = 20 # Not used for update
            search = filters.get('search')
            status = filters.get('status')
            not_status = filters.get('not_status')
            days_old = filters.get('days_old')
            salary = filters.get('salary')
            order = filters.get('order') # Not used for update but part of params
            sql_filter = filters.get('sql_filter')
            # Extract boolean filters
            boolean_keys = [
                'flagged', 'like', 'ignored', 'seen', 'applied', 'discarded', 'closed',
                'interview_rh', 'interview', 'interview_tech', 'interview_technical_test',
                'interview_technical_test_done', 'ai_enriched', 'easy_apply']
            boolean_filters = {k: filters.get(k) for k in boolean_keys}
            where, params = self.repo.build_where(
                search, status, not_status, days_old, salary, sql_filter, boolean_filters)
            return self.repo.update_jobs_by_filter(where, params, update_data)
        elif ids:
            return self.repo.update_jobs_by_ids(ids, update_data)
        return 0

    def delete_jobs(self, ids: Optional[List[int]] = None, filters: Optional[Dict[str, Any]] = None, select_all: bool = False) -> int:
        """
        Deletes multiple jobs.
        If select_all is True and filters are provided, deletes all jobs matching the filters.
        Otherwise, deletes the jobs specified in ids.
        """
        if select_all and filters:
            # Extract filter parameters matching list_jobs signature
            page = 1 # Not used 
            size = 20 # Not used 
            search = filters.get('search')
            status = filters.get('status')
            not_status = filters.get('not_status')
            days_old = filters.get('days_old')
            salary = filters.get('salary')
            order = filters.get('order') # Not used 
            sql_filter = filters.get('sql_filter')
            # Extract boolean filters
            boolean_filters = {k: filters.get(k) for k in JOB_BOOLEAN_KEYS}
            where, params = self.repo.build_where(
                search, status, not_status, days_old, salary, sql_filter, boolean_filters
            )
            return self.repo.delete_jobs_by_filter(where, params)
        elif ids:
            return self.repo.delete_jobs_by_ids(ids)
        return 0
