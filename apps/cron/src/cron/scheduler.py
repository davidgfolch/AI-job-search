from datetime import datetime, timedelta, timezone
import re

from cron import config
from commonlib.repositories.cron_state_repository import CronStateRepository
from commonlib.terminalColor import green, yellow, red


def _parse_cadency(cadency: str) -> int:
    match = re.match(r'(\d+)([smhd])', cadency.strip().lower())
    if not match:
        return 3600
    num = int(match.group(1))
    unit = match.group(2)
    return {"s": num, "m": num * 60, "h": num * 3600, "d": num * 86400}[unit]


class CronJob:
    name: str
    cadency: str

    def run(self, cron_state: CronStateRepository):
        raise NotImplementedError


class Scheduler:
    def __init__(self, cron_state: CronStateRepository, jobs: list[CronJob]):
        self._cron_state = cron_state
        self._jobs = jobs
        self._is_first_tick = True

    def tick(self):
        now = datetime.now(timezone.utc)
        for job in self._jobs:
            state = self._cron_state.get_state(job.name) or {}
            last_run = state.get("last_run_at")
            was_error = state.get("status") == "error"
            if last_run is None or was_error or self._is_first_tick:
                should_run = True
            else:
                if isinstance(last_run, str):
                    last_run = last_run.replace("Z", "+00:00")
                    last_run = datetime.fromisoformat(last_run if "+" in last_run else last_run + "+00:00")
                cadency_seconds = _parse_cadency(job.cadency)
                should_run = (now - last_run).total_seconds() >= cadency_seconds

            if should_run:
                print(green(f"[scheduler] running job '{job.name}'"))
                try:
                    job.run(self._cron_state)
                except Exception as e:
                    print(red(f"[scheduler] job '{job.name}' FAILED: {e}"))
                    self._cron_state.update_state(job.name, {
                        "last_run_at": now,
                        "status": "error",
                        "error": str(e),
                    })
                else:
                    print(green(f"[scheduler] job '{job.name}' completed OK"))
                    self._cron_state.update_state(job.name, {
                        "last_run_at": now,
                        "status": "ok",
                    })
        self._is_first_tick = False
