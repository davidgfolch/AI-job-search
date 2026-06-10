import time
from datetime import datetime

from cron import config
from cron.scheduler import Scheduler
from commonlib.mongodb_provider import get_mongo_provider
from commonlib.repositories.cron_state_repository import CronStateRepository
from commonlib.terminalColor import green, yellow, cyan
from cron.jobs.company_salary_history.job import CompanySalaryHistoryJob


def run():
    print(cyan(f"[cron] starting at {datetime.utcnow().isoformat()}"))

    provider = get_mongo_provider(config.MONGO_READ_URI, config.MONGO_WRITE_URI, config.MONGO_DATABASE)
    cron_state = CronStateRepository(provider)

    jobs = [
        CompanySalaryHistoryJob(cadency=config.CRON_SALARY_CADENCY),
    ]

    scheduler = Scheduler(cron_state, jobs)

    print(green(f"[cron] {len(jobs)} job(s) registered, checking every {config.CHECK_INTERVAL_SECONDS}s"))
    for j in jobs:
        print(green(f"[cron]   -> {j.name} (cadency={j.cadency})"))

    tick = 0
    while True:
        tick += 1
        print(yellow(f"[cron] tick #{tick} at {datetime.utcnow().isoformat()}"))
        scheduler.tick()
        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
