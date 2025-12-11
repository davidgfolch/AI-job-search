from typing import Optional, Dict, Any, List
from repositories.jobs_repository import JobsRepository


class JobsService:
    def __init__(self, repo: JobsRepository = None):
        self.repo = repo or JobsRepository()

    def list_jobs(self, page: int, size: int, search: Optional[str] = None,
                    status: Optional[str] = None, not_status: Optional[str] = None,
                    days_old: Optional[int] = None, salary: Optional[str] = None,
                    order: Optional[str] = "created desc", boolean_filters: Dict[str, Optional[bool]] = None,
                    sql_filter: Optional[str] = None) -> Dict[str, Any]:
        return self.repo.list_jobs(page, size, search, status, not_status,
            days_old, salary, order, boolean_filters, sql_filter)

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
            if len(part1) > 2 and part1 not in ['grupo']:
                regex_lookup = f'(^| ){part1}($| )'
                try:
                    rows = self.repo.find_applied_jobs_by_regex(regex_lookup)
                except Exception:
                    pass
        return rows
