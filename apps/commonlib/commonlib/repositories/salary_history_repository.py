import re
from datetime import datetime
from commonlib.mongodb_provider import MongoDbProvider
from commonlib.company_matcher import get_best_candidate


class SalaryHistoryRepository:
    def __init__(self, mongo_provider: MongoDbProvider):
        self._db = mongo_provider

    def get_job_history(self, job_id: int) -> list[dict]:
        col = self._db.get_database(write=False)["company_salary_history"]
        return list(col.find({"job_id": job_id}, {"_id": 0}).sort("recorded_at", -1).limit(50))

    def get_company_history(self, company_normalized: str) -> list[dict]:
        col = self._db.get_database(write=False)["company_salary_history"]

        results = list(col.find(
            {"company_normalized": {"$regex": f"^{re.escape(company_normalized)}$"}},
            {"_id": 0}
        ).sort("recorded_at", -1).limit(200))
        if results:
            return results

        candidate = get_best_candidate(company_normalized)
        if candidate:
            results = list(col.find(
                {"company_normalized": {"$regex": f"^{re.escape(candidate)}"}},
                {"_id": 0}
            ).sort("recorded_at", -1).limit(200))
            if results:
                return results

        return []

    def get_last_record(self, job_id: int) -> dict | None:
        col = self._db.get_database(write=False)["company_salary_history"]
        return col.find_one({"job_id": job_id}, {"_id": 0}, sort=[("recorded_at", -1)])

    def record_exists(self, job_id: int, salary: str, recorded_at: datetime) -> bool:
        col = self._db.get_database(write=False)["company_salary_history"]
        return col.find_one({"job_id": job_id, "salary": salary, "recorded_at": recorded_at}) is not None

    def save_record(self, record: dict):
        col = self._db.get_database(write=True)["company_salary_history"]
        col.insert_one(record)

    def save_records(self, records: list[dict]) -> int:
        if not records:
            return 0
        col = self._db.get_database(write=True)["company_salary_history"]
        try:
            result = col.insert_many(records, ordered=False)
            return len(result.inserted_ids)
        except Exception:
            return 0
