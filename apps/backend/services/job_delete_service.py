from typing import Optional, Dict, Any, List, Callable
from repositories.jobDeleteRepository import JobDeleteRepository
from repositories.queries.jobs_query_builder import build_jobs_where_clause
from commonlib.jobSnapshotRepository import JobSnapshotRepository
from utils.filter_parser import extract_filter_params


class JobDeleteService:
    def __init__(self, get_job_callback: Optional[Callable] = None):
        self.delete_repo = JobDeleteRepository()
        self._get_job = get_job_callback

    def _build_snapshot_queries(self, jobs: List[Dict[str, Any]]) -> List[tuple]:
        snapshot_queries = []
        for job in jobs:
            query, snapshot_params = JobSnapshotRepository.build_snapshot_query_and_params(job, "DELETED")
            snapshot_queries.append((query, snapshot_params))
        return snapshot_queries

    def delete_by_filters(self, filters: Dict[str, Any]) -> int:
        params = extract_filter_params(filters)
        where, db_params = build_jobs_where_clause(**params)
        jobs_to_delete = self.delete_repo.get_jobs_by_filter(where, db_params)
        snapshot_queries = self._build_snapshot_queries(jobs_to_delete)
        return self.delete_repo.delete_jobs_with_snapshots(where, db_params, snapshot_queries)

    def update_jobs_by_filter(self, where: List[str], db_params: List[Any], update_data: Dict[str, Any]) -> int:
        return self.delete_repo.update_jobs_by_filter(where, db_params, update_data)

    def update_jobs_by_ids(self, ids: List[int], update_data: Dict[str, Any]) -> int:
        return self.delete_repo.update_jobs_by_ids(ids, update_data)

    def delete_by_ids(self, ids: List[int]) -> int:
        snapshot_queries = []
        for job_id in ids:
            job = self._get_job(job_id) if self._get_job else None
            if job:
                query, snapshot_params = JobSnapshotRepository.build_snapshot_query_and_params(job, "DELETED")
                snapshot_queries.append((query, snapshot_params))
        return self.delete_repo.delete_jobs_with_snapshots(
            ["id IN (" + ", ".join(["%s"] * len(ids)) + ")"], ids, snapshot_queries
        )
