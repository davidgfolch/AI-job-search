from datetime import datetime

from cron.scheduler import CronJob
from cron import config
from commonlib.mongodb_provider import get_mongo_provider
from commonlib.repositories.cron_state_repository import CronStateRepository
from commonlib.repositories.salary_history_repository import SalaryHistoryRepository
from commonlib.terminalColor import green, yellow
from cron.jobs.company_salary_history.scanner import CompanySalaryHistoryScanner


class CompanySalaryHistoryJob(CronJob):
    def __init__(self, cadency: str = "1h"):
        self.name = "companySalaryHistory"
        self.cadency = cadency

    def run(self, cron_state: CronStateRepository):
        provider = get_mongo_provider(config.MONGO_READ_URI, config.MONGO_WRITE_URI, config.MONGO_DATABASE)
        salary_repo = SalaryHistoryRepository(provider)
        scanner = CompanySalaryHistoryScanner(salary_repo)

        state = cron_state.get_state(self.name) or {}
        last_id = state.get("last_job_id", 0)
        last_run = state.get("last_run_at")

        print(yellow(f"[{self.name}] scanning from last_job_id={last_id}, last_run_at={last_run or 'N/A'}"))
        result = scanner.run(last_job_id=last_id, last_run_at=last_run)

        cron_state.update_state(self.name, {"last_job_id": result['last_job_id']})

        if result['records_added'] > 0:
            print(green(f"[{self.name}] processed up to job_id={result['last_job_id']}, "
                        f"records_added={result['records_added']}"))
        else:
            print(yellow(f"[{self.name}] no new records found (up to job_id={result['last_job_id']})"))
