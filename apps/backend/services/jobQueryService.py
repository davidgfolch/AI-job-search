from typing import Optional, Dict, Any, List
from commonlib.observability import get_logger
from repositories.jobQueryRepository import JobQueryRepository
from commonlib.company_matcher import search_partial_company
from services.company_synonym_service import CompanySynonymService

logger = get_logger("backend.services.jobQueryService")


class JobQueryService:
    def __init__(self, synonym_service: Optional[CompanySynonymService] = None):
        self.query_repo = JobQueryRepository()
        self._synonym_service = synonym_service

    @property
    def synonym_service(self) -> CompanySynonymService:
        if self._synonym_service is None:
            self._synonym_service = CompanySynonymService()
        return self._synonym_service

    def _get_search_companies(self, company_raw: str) -> List[str]:
        try:
            synonyms = self.synonym_service.get_synonyms(company_raw)
            return [company_raw] + synonyms
        except Exception as e:
            logger.warning("synonyms.lookup_failed", error=str(e))
            return [company_raw]

    def get_applied_jobs_by_company_name(
        self, company: str, client: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not company or not company.strip():
            raise ValueError("Company name must be a non-empty string")
        company_raw = company.lower().replace("'", "''")
        if company_raw == "joppy" and client:
            rows = self.query_repo.find_applied_by_company(client, client)
        else:
            search_companies = self._get_search_companies(company_raw)
            rows = self.query_repo.find_applied_by_companies(search_companies)
        if not rows:
            regexes = []
            search_list = [company_raw]
            if not (company_raw == "joppy" and client):
                search_list = self._get_search_companies(company_raw)
            for c in search_list:
                regex = search_partial_company(c)
                if regex:
                    regexes.append(regex)
            if regexes:
                try:
                    rows = self.query_repo.find_applied_jobs_by_regex(regexes)
                except Exception as e:
                    logger.warning("jobs.regex_search_failed", error=str(e), regex_count=len(regexes))
                    rows = []
        return [
            {"id": row[0], "created": row[1].isoformat() if row[1] else None}
            for row in (rows or [])
        ]
