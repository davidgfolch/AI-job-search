from commonlib.sql.mysqlUtil import MysqlUtil, getConnection
from commonlib.repositories.salary_history_repository import SalaryHistoryRepository
from commonlib.company_normalizer import normalize_company_name
from commonlib.observability import get_logger

logger = get_logger("cron.jobs.company_salary_history.scanner")


class CompanySalaryHistoryScanner:
    def __init__(self, salary_repo: SalaryHistoryRepository):
        self._salary_repo = salary_repo

    def run(self, last_job_id: int = 0, last_run_at: str | None = None) -> dict:
        total = 0
        max_id = last_job_id

        with MysqlUtil(getConnection()) as mysql:
            new_rows = self._fetch_jobs(mysql, last_job_id)
            if new_rows:
                logger.info("cron.scanner.jobs_fetched", rows=len(new_rows), after_job_id=last_job_id)
                records = []
                for row in new_rows:
                    job_id, title, company, salary, changed_at = row
                    records.append({
                        "job_id": job_id,
                        "company_raw": company,
                        "company_normalized": normalize_company_name(company),
                        "title": title,
                        "salary": salary,
                        "recorded_at": changed_at,
                        "source": "backfill" if last_job_id == 0 else "incremental",
                    })
                    max_id = max(max_id, job_id)
                saved = self._salary_repo.save_records(records)
                total += saved
                logger.info("cron.scanner.records_saved", saved=saved, records=len(records), backfill=last_job_id == 0)
            else:
                logger.debug("cron.scanner.no_new_jobs", after_job_id=last_job_id)

            if last_run_at:
                updated_rows = self._fetch_updated(mysql, last_run_at, max_id)
                if updated_rows:
                    logger.info("cron.scanner.updates_checked", rows=len(updated_rows), since=last_run_at)
                    for row in updated_rows:
                        job_id, title, company, salary, changed_at = row
                        last_rec = self._salary_repo.get_last_record(job_id)
                        if last_rec is None or last_rec.get("salary") != salary:
                            action = "new" if last_rec is None else "changed"
                            self._salary_repo.save_record({
                                "job_id": job_id,
                                "company_raw": company,
                                "company_normalized": normalize_company_name(company),
                                "title": title,
                                "salary": salary,
                                "recorded_at": changed_at,
                                "source": "incremental",
                            })
                            total += 1
                            logger.debug("cron.scanner.salary_recorded", job_id=job_id, action=action, salary=salary, previous_salary=None if last_rec is None else last_rec.get("salary"))
                    logger.info("cron.scanner.updates_saved", records=total)

        return {
            "last_job_id": max_id,
            "records_added": total,
        }

    def _fetch_jobs(self, mysql: MysqlUtil, after_id: int) -> list[tuple]:
        query = """
            SELECT id, title, company, salary, COALESCE(modified, created) as changed_at
            FROM jobs
            WHERE salary IS NOT NULL AND salary != '' AND id > %s
            ORDER BY id
        """
        return mysql.fetchAll(query, (after_id,))

    def _fetch_updated(self, mysql: MysqlUtil, since: str, exclude_upto: int) -> list[tuple]:
        query = """
            SELECT id, title, company, salary, COALESCE(modified, created) as changed_at
            FROM jobs
            WHERE salary IS NOT NULL AND salary != ''
              AND modified > %s
              AND id <= %s
            ORDER BY id
        """
        return mysql.fetchAll(query, (since, exclude_upto))
