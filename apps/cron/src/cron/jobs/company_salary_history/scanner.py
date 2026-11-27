from commonlib.company_normalizer import normalize_company_name
from commonlib.observability import get_logger
from commonlib.repositories.job_salary_repository import JobSalaryRepository
from commonlib.repositories.salary_history_repository import SalaryHistoryRepository

logger = get_logger("cron.jobs.company_salary_history.scanner")


class CompanySalaryHistoryScanner:
    def __init__(self, salary_repo: SalaryHistoryRepository, job_repo: JobSalaryRepository):
        self._salary_repo = salary_repo
        self._job_repo = job_repo

    def run(self, last_job_id: int = 0, last_run_at: str | None = None) -> dict:
        total = 0
        max_id = last_job_id
        new_rows = self._job_repo.fetch_salary_jobs_after(last_job_id)
        if new_rows:
            logger.info("cron.scanner.jobs_fetched", rows=len(new_rows), after_job_id=last_job_id)
            records = []
            for row in new_rows:
                job_id = row[0]
                records.append(self._build_record(row, "backfill" if last_job_id == 0 else "incremental"))
                max_id = max(max_id, job_id)
            saved = self._salary_repo.save_records(records)
            total += saved
            logger.info("cron.scanner.records_saved", saved=saved, records=len(records), backfill=last_job_id == 0)
        else:
            logger.debug("cron.scanner.no_new_jobs", after_job_id=last_job_id)

        if last_run_at:
            updated_rows = self._job_repo.fetch_updated_salary_jobs(last_run_at, max_id)
            if updated_rows:
                logger.info("cron.scanner.updates_checked", rows=len(updated_rows), since=last_run_at)
                for row in updated_rows:
                    job_id = row[0]
                    salary = row[3]
                    last_rec = self._salary_repo.get_last_record(job_id)
                    if last_rec is None or last_rec.get("salary") != salary:
                        action = "new" if last_rec is None else "changed"
                        self._salary_repo.save_record(self._build_record(row, "incremental"))
                        total += 1
                        logger.debug("cron.scanner.salary_recorded", job_id=job_id, action=action, salary=salary, previous_salary=None if last_rec is None else last_rec.get("salary"))
                logger.info("cron.scanner.updates_saved", records=total)

        return {"last_job_id": max_id, "records_added": total}

    @staticmethod
    def _build_record(row: tuple, source: str) -> dict:
        job_id, title, company, salary, changed_at = row
        return {
            "job_id": job_id,
            "company_raw": company,
            "company_normalized": normalize_company_name(company),
            "title": title,
            "salary": salary,
            "recorded_at": changed_at,
            "source": source,
        }
