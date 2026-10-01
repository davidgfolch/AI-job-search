from datetime import datetime

from cron.scheduler import CronJob
from cron import config
from commonlib.mongodb_provider import get_mongo_provider
from commonlib.observability import get_logger
from commonlib.repositories.cron_state_repository import CronStateRepository
from commonlib.repositories.salary_history_repository import SalaryHistoryRepository
from cron.jobs.company_salary_history.scanner import CompanySalaryHistoryScanner

logger = get_logger("cron.jobs.company_salary_history.job")


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

        logger.info("cron.scan_started", job=self.name, last_job_id=last_id, last_run_at=last_run)
        result = scanner.run(last_job_id=last_id, last_run_at=last_run)

        cron_state.update_state(self.name, {"last_job_id": result['last_job_id']})

        if result['records_added'] > 0:
            logger.info("cron.scan_completed", job=self.name, last_job_id=result['last_job_id'], records_added=result['records_added'])
        else:
            logger.debug("cron.scan_no_records", job=self.name, last_job_id=result['last_job_id'])
