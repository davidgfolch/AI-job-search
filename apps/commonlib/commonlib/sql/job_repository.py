from typing import Any

QRY_INSERT = """
INSERT INTO jobs (
    jobId,title,company,location,url,markdown,easy_apply,web_page,duplicated_id)
          values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

QRY_FIND_JOB_BY_JOB_ID = """
SELECT id,jobId FROM jobs WHERE jobId = %s"""


class JobRepository:
    """Repository for job-specific database operations."""

    def __init__(self, execute_transaction: callable, execute_query: callable):
        self._execute_transaction = execute_transaction
        self._execute_query = execute_query

    def insert(self, params: tuple) -> int | None:
        """
        Insert a job record into the database.

        Args:
            params: Tuple of job field values in order

        Returns:
            Last inserted row ID, or None on error
        """
        try:
            return self._execute_transaction(
                lambda c: (c.execute(QRY_INSERT, params), c.lastrowid)[1]
            )
        except Exception:
            from commonlib.sqlUtil import error
            error(Exception('Insert failed'))
            return None

    def job_exists(self, job_id: str) -> bool:
        """Check if job exists in database by job_id."""
        existing = self._execute_query(
            lambda c: (c.execute(QRY_FIND_JOB_BY_JOB_ID, [job_id]), c.fetchone())[1]
        )
        return existing is not None

    def insert_job(self, job_data: dict[str, Any]) -> int | None:
        """
        Insert job data and return row ID if successful.

        Args:
            job_data: Dict with job fields (job_id, title, company, etc.)

        Returns:
            Last inserted row ID, or None on error
        """
        params = (
            job_data.get('job_id', ''),
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('url', ''),
            job_data.get('markdown', ''),
            job_data.get('easy_apply', False),
            job_data.get('web_page', ''),
            job_data.get('duplicated_id', None)
        )
        return self.insert(params)
