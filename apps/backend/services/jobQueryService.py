from typing import Optional, Dict, Any, List
from repositories.jobQueryRepository import JobQueryRepository
from utils.job_utils import search_partial_company


class JobQueryService:
    def __init__(self):
        self.query_repo = JobQueryRepository()

    def get_applied_jobs_by_company_name(
        self, company: str, client: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not company or not company.strip():
            raise ValueError("Company name must be a non-empty string")
        company_raw = company.lower().replace("'", "''")
        rows = (
            self.query_repo.find_applied_by_company(client, client)
            if company_raw == "joppy" and client
            else self.query_repo.find_applied_by_company(company_raw)
        )
        if not rows:
            regex = search_partial_company(company_raw)
            if regex:
                try:
                    rows = self.query_repo.find_applied_jobs_by_regex(regex)
                except Exception:
                    rows = []
        return [
            {"id": row[0], "created": row[1].isoformat() if row[1] else None}
            for row in rows
        ]
