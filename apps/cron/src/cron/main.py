import time

from cron import config
from cron.scheduler import Scheduler
from commonlib.mongodb_provider import get_mongo_provider
from commonlib.observability import configure_logging, get_logger
from commonlib.repositories.cron_state_repository import CronStateRepository
from cron.jobs.company_salary_history.job import CompanySalaryHistoryJob

logger = get_logger("cron.main")


def run():
    configure_logging("cron")
    logger.info("cron.started")

    provider = get_mongo_provider(config.MONGO_READ_URI, config.MONGO_WRITE_URI, config.MONGO_DATABASE)
    cron_state = CronStateRepository(provider)

    jobs = [
        CompanySalaryHistoryJob(cadency=config.CRON_SALARY_CADENCY),
    ]

    scheduler = Scheduler(cron_state, jobs)

    logger.info("cron.jobs_registered", jobs=len(jobs), check_interval_seconds=config.CHECK_INTERVAL_SECONDS)
    for j in jobs:
        logger.debug("cron.job_registered", job=j.name, cadency=j.cadency)

    tick = 0
    while True:
        tick += 1
        logger.info("cron.tick", tick=tick)
        scheduler.tick()
        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
