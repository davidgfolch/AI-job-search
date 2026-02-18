from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List

from commonlib.mysqlUtil import MysqlUtil, getConnection


class JobSnapshotRepository:
    def __init__(self, mysql: MysqlUtil = None):
        self.mysql = mysql if mysql else MysqlUtil(getConnection())

    @staticmethod
    def build_snapshot_query_and_params(
        job_data: dict,
        snapshot_reason: str,
    ) -> Tuple[str, Dict[str, Any]]:
        query = """
            INSERT INTO job_snapshots (
                job_id, platform, original_created_at, snapshot_at, snapshot_reason,
                title, company, location, salary,
                applied, discarded, interview, interview_rh, interview_tech, interview_technical_test,
                web_page
            ) VALUES (
                %(job_id)s, %(platform)s, %(original_created_at)s, %(snapshot_at)s, %(snapshot_reason)s,
                %(title)s, %(company)s, %(location)s, %(salary)s,
                %(applied)s, %(discarded)s, %(interview)s, %(interview_rh)s, %(interview_tech)s, %(interview_technical_test)s,
                %(web_page)s
            )
        """
        params = {
            "job_id": job_data.get("jobId"),
            "platform": job_data.get("web_page"),
            "original_created_at": job_data.get("created"),
            "snapshot_at": datetime.now(),
            "snapshot_reason": snapshot_reason,
            "title": job_data.get("title"),
            "company": job_data.get("company"),
            "location": job_data.get("location"),
            "salary": job_data.get("salary"),
            "applied": bool(job_data.get("applied")),
            "discarded": bool(job_data.get("discarded")),
            "interview": bool(job_data.get("interview")),
            "interview_rh": bool(job_data.get("interview_rh")),
            "interview_tech": bool(job_data.get("interview_tech")),
            "interview_technical_test": bool(job_data.get("interview_technical_test")),
            "web_page": job_data.get("web_page"),
        }
        return query, params

    def save_snapshot(
        self,
        job_id: str,
        platform: Optional[str],
        original_created_at: Optional[datetime],
        snapshot_reason: str,
        title: Optional[str],
        company: Optional[str],
        location: Optional[str],
        salary: Optional[str],
        applied: bool,
        discarded: bool,
        interview: bool,
        interview_rh: bool,
        interview_tech: bool,
        interview_technical_test: bool,
        web_page: Optional[str],
    ) -> int:
        query = """
            INSERT INTO job_snapshots (
                job_id, platform, original_created_at, snapshot_at, snapshot_reason,
                title, company, location, salary,
                applied, discarded, interview, interview_rh, interview_tech, interview_technical_test,
                web_page
            ) VALUES (
                %(job_id)s, %(platform)s, %(original_created_at)s, %(snapshot_at)s, %(snapshot_reason)s,
                %(title)s, %(company)s, %(location)s, %(salary)s,
                %(applied)s, %(discarded)s, %(interview)s, %(interview_rh)s, %(interview_tech)s, %(interview_technical_test)s,
                %(web_page)s
            )
        """
        params = {
            "job_id": job_id,
            "platform": platform,
            "original_created_at": original_created_at,
            "snapshot_at": datetime.now(),
            "snapshot_reason": snapshot_reason,
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "applied": applied,
            "discarded": discarded,
            "interview": interview,
            "interview_rh": interview_rh,
            "interview_tech": interview_tech,
            "interview_technical_test": interview_technical_test,
            "web_page": web_page,
        }
        return self.mysql.executeAndCommit(query, params)

    def get_snapshots_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list:
        query = """
            SELECT id, job_id, platform, original_created_at, snapshot_at, snapshot_reason,
                   title, company, location, salary,
                   applied, discarded, interview, interview_rh, interview_tech, interview_technical_test,
                   web_page
            FROM job_snapshots
            WHERE snapshot_at BETWEEN %(start_date)s AND %(end_date)s
            ORDER BY snapshot_at DESC
        """
        return self.mysql.fetchAll(
            query, {"start_date": start_date, "end_date": end_date}
        )

    def get_snapshots_by_reason(self, reason: str) -> list:
        query = """
            SELECT id, job_id, platform, original_created_at, snapshot_at, snapshot_reason,
                   title, company, location, salary,
                   applied, discarded, interview, interview_rh, interview_tech, interview_technical_test,
                   web_page
            FROM job_snapshots
            WHERE snapshot_reason = %(reason)s
            ORDER BY snapshot_at DESC
        """
        return self.mysql.fetchAll(query, {"reason": reason})

    def get_snapshots_by_platform(self, platform: str) -> list:
        query = """
            SELECT id, job_id, platform, original_created_at, snapshot_at, snapshot_reason,
                   title, company, location, salary,
                   applied, discarded, interview, interview_rh, interview_tech, interview_technical_test,
                   web_page
            FROM job_snapshots
            WHERE platform = %(platform)s
            ORDER BY snapshot_at DESC
        """
        return self.mysql.fetchAll(query, {"platform": platform})

    def count_snapshots_by_reason(self, reason: str) -> int:
        query = "SELECT COUNT(*) FROM job_snapshots WHERE snapshot_reason = %(reason)s"
        rows = self.mysql.fetchAll(query, {"reason": reason})
        return rows[0][0] if rows else 0

    def count_snapshots_by_platform(self, platform: str) -> int:
        query = "SELECT COUNT(*) FROM job_snapshots WHERE platform = %(platform)s"
        rows = self.mysql.fetchAll(query, {"platform": platform})
        return rows[0][0] if rows else 0

    def get_all_snapshots(self, limit: int = 1000, offset: int = 0) -> list:
        query = """
            SELECT id, job_id, platform, original_created_at, snapshot_at, snapshot_reason,
                   title, company, location, salary,
                   applied, discarded, interview, interview_rh, interview_tech, interview_technical_test,
                   web_page
            FROM job_snapshots
            ORDER BY snapshot_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        return self.mysql.fetchAll(query, {"limit": limit, "offset": offset})

    def delete_snapshots_older_than(self, days: int) -> int:
        query = """
            DELETE FROM job_snapshots
            WHERE snapshot_at < DATE_SUB(NOW(), INTERVAL %(days)s DAY)
        """
        return self.mysql.executeAndCommit(query, {"days": days})
