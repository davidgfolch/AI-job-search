from datetime import datetime
from typing import Optional

from commonlib.jobSnapshotRepository import JobSnapshotRepository


class JobSnapshotService:
    def __init__(self):
        self.repo = JobSnapshotRepository()

    def create_snapshot_from_job(
        self,
        job_data: dict,
        snapshot_reason: str,
    ) -> int:
        return self.repo.save_snapshot(
            job_id=job_data.get("jobId"),
            platform=job_data.get("web_page"),
            original_created_at=job_data.get("created"),
            snapshot_reason=snapshot_reason,
            title=job_data.get("title"),
            company=job_data.get("company"),
            location=job_data.get("location"),
            salary=job_data.get("salary"),
            applied=bool(job_data.get("applied")),
            discarded=bool(job_data.get("discarded")),
            interview=bool(job_data.get("interview")),
            interview_rh=bool(job_data.get("interview_rh")),
            interview_tech=bool(job_data.get("interview_tech")),
            interview_technical_test=bool(job_data.get("interview_technical_test")),
            web_page=job_data.get("web_page"),
        )

    def snapshot_before_delete(self, job_data: dict) -> int:
        return self.create_snapshot_from_job(job_data, "DELETED")

    def snapshot_on_applied(self, job_data: dict) -> int:
        return self.create_snapshot_from_job(job_data, "APPLIED")

    def snapshot_on_interview(self, job_data: dict) -> int:
        return self.create_snapshot_from_job(job_data, "INTERVIEW")

    def snapshot_on_discarded(self, job_data: dict) -> int:
        return self.create_snapshot_from_job(job_data, "DISCARDED")

    def get_snapshots_by_date_range(self, start_date: datetime, end_date: datetime):
        return self.repo.get_snapshots_by_date_range(start_date, end_date)

    def get_snapshots_by_reason(self, reason: str):
        return self.repo.get_snapshots_by_reason(reason)

    def get_snapshots_by_platform(self, platform: str):
        return self.repo.get_snapshots_by_platform(platform)

    def get_all_snapshots(self, limit: int = 1000, offset: int = 0):
        return self.repo.get_all_snapshots(limit, offset)
