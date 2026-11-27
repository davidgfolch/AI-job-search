from commonlib.sql.mysqlUtil import MysqlUtil

SALARY_JOBS_AFTER_QUERY = """SELECT id, title, company, salary, COALESCE(modified, created) as changed_at
            FROM jobs
            WHERE salary IS NOT NULL AND salary != '' AND id > %s
            ORDER BY id"""

UPDATED_SALARY_JOBS_QUERY = """SELECT id, title, company, salary, COALESCE(modified, created) as changed_at
            FROM jobs
            WHERE salary IS NOT NULL AND salary != ''
              AND modified > %s
              AND id <= %s
            ORDER BY id"""


class JobSalaryRepository:
    """Owns the read-only `jobs` queries used by the salary-history scanner."""

    def __init__(self, mysql: MysqlUtil = None):
        self._mysql = mysql if mysql else MysqlUtil()

    def fetch_salary_jobs_after(self, after_id: int) -> list[tuple]:
        return self._mysql.fetchAll(SALARY_JOBS_AFTER_QUERY, (after_id,))

    def fetch_updated_salary_jobs(self, since: str, upto_id: int) -> list[tuple]:
        return self._mysql.fetchAll(UPDATED_SALARY_JOBS_QUERY, (since, upto_id))
