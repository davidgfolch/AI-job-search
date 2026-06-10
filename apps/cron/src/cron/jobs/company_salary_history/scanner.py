from commonlib.sql.mysqlUtil import MysqlUtil, getConnection
from commonlib.repositories.salary_history_repository import SalaryHistoryRepository
from commonlib.company_normalizer import normalize_company_name
from commonlib.terminalColor import green, yellow, cyan


class CompanySalaryHistoryScanner:
    def __init__(self, salary_repo: SalaryHistoryRepository):
        self._salary_repo = salary_repo

    def run(self, last_job_id: int = 0, last_run_at: str | None = None) -> dict:
        total = 0
        max_id = last_job_id

        with MysqlUtil(getConnection()) as mysql:
            new_rows = self._fetch_jobs(mysql, last_job_id)
            if new_rows:
                print(cyan(f"[scanner] fetched {len(new_rows)} new jobs (id > {last_job_id})"))
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
                print(green(f"[scanner] saved {saved}/{len(records)} salary records (backfill={last_job_id == 0})"))
            else:
                print(yellow(f"[scanner] no new jobs found (id > {last_job_id})"))

            if last_run_at:
                updated_rows = self._fetch_updated(mysql, last_run_at, max_id)
                if updated_rows:
                    print(cyan(f"[scanner] checking {len(updated_rows)} updated jobs since {last_run_at}"))
                    for row in updated_rows:
                        job_id, title, company, salary, changed_at = row
                        last_rec = self._salary_repo.get_last_record(job_id)
                        if last_rec is None or last_rec.get("salary") != salary:
                            action = "new" if last_rec is None else f"changed '{last_rec.get('salary')}' -> '{salary}'"
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
                            print(green(f"[scanner]   job_id={job_id}: salary {action}"))
                    print(green(f"[scanner] saved {total} updated salary records"))

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
