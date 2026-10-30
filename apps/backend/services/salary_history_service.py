import os

from commonlib.company_normalizer import normalize_company_name
from commonlib.mongo_config import resolve_mongo_uri
from commonlib.mongodb_provider import get_mongo_provider
from commonlib.repositories.salary_history_repository import SalaryHistoryRepository


MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:rootPass@localhost:27017/")
MONGO_READ_URI = os.getenv("MONGO_READ_URI") or MONGO_URI
MONGO_WRITE_URI = os.getenv("MONGO_WRITE_URI") or MONGO_URI
MONGO_DB = os.getenv("MONGO_DATABASE", "jobs")

_repo: SalaryHistoryRepository | None = None


def _repository() -> SalaryHistoryRepository:
    """Build the Mongo repository on first use, resolving host/LAN discovery."""
    global _repo
    if _repo is None:
        provider = get_mongo_provider(resolve_mongo_uri(MONGO_READ_URI), resolve_mongo_uri(MONGO_WRITE_URI), MONGO_DB)
        _repo = SalaryHistoryRepository(provider)
    return _repo


class SalaryHistoryService:
    def get_job_history(self, job_id: int) -> list[dict]:
        return _repository().get_job_history(job_id)

    def get_company_history(self, company_raw: str) -> list[dict]:
        normalized = normalize_company_name(company_raw)
        if not normalized:
            return []
        return _repository().get_company_history(normalized)

    def delete_record(self, record_id: str) -> bool:
        return _repository().delete_record(record_id)
