from typing import Any, Optional, Tuple
from datetime import datetime
from commonlib.dateUtil import getDatetimeNow, getTimeUnits, parseDatetime, getSeconds, getDatetimeNowStr
from commonlib.environmentUtil import getEnvByPrefix
from scrapper.core.scrapper_config import TIMER
from scrapper.util.persistence_manager import PersistenceManager

class ScrapperStateCalculator:
    def __init__(self, name: str, properties: dict, persistence_manager: PersistenceManager):
        self.name = name
        self.properties = properties
        self.persistence_manager = persistence_manager

    def resolve_timer(self, default_timer: int) -> tuple[int, str]:
        prefix = f"{self.name.upper()}_RUN_CADENCY_"
        current_ts = getDatetimeNow()
        current_hour = datetime.fromtimestamp(current_ts).hour
        env_vars = getEnvByPrefix(prefix)
        for suffix, value in env_vars.items():
            parts = suffix.split('-')
            if len(parts) == 2:
                start = int(parts[0])
                end = int(parts[1])
                if start <= end:
                    if start <= current_hour <= end:
                        return getSeconds(value), suffix
                else:
                    raise ValueError(f"Invalid hour range: {suffix}")
            else:
                raise ValueError(f"Invalid hour range: {suffix}")
        return default_timer, "Default"

    def _calculate_error_penalty(self) -> tuple[int, str, int, bool]:
        """
        Calculates if there is an active error penalty.
        Returns: (timeoutSeconds, timer_details, seconds_remaining, error_penalty_wait)
        """
        last_error_time = self.persistence_manager.get_state(self.name).get('last_error_time')
        if last_error_time:
            lapsed_error = getDatetimeNow() - parseDatetime(last_error_time)
            if lapsed_error < 1800:
                seconds_remaining = max(0, 1800 - lapsed_error)
                return 1800, "Error Wait", int(seconds_remaining), True
        return 0, "Unknown", 0, False

    def _calculate_standard_wait(self, last_exec_time: Optional[str]) -> tuple[int, str, int]:
        """
        Calculates standar wait time based on last execution and failed keywords.
        Returns: (timeoutSeconds, timer_details, seconds_remaining)
        """
        failed_keywords = self.persistence_manager.get_failed_keywords(self.name)
        if last_exec_time:
            lapsed = getDatetimeNow() - parseDatetime(last_exec_time)
            if failed_keywords:
                timeoutSeconds = 900 # 15 minutes retry
                timer_details = f"Retry({len(failed_keywords)})"
            else:
                timeoutSeconds, timer_details = self.resolve_timer(self.properties[TIMER])
            seconds_remaining = max(0, timeoutSeconds - lapsed)
        else:
            timeoutSeconds, timer_details = self.resolve_timer(self.properties[TIMER])
            seconds_remaining = 0
        return timeoutSeconds, timer_details, int(seconds_remaining)

    def _calculate_status_and_display(self, starting: bool, startingAt: str, seconds_remaining: int, error_penalty_wait: bool) -> tuple[int, str, str]:
        """
        Calculates final status message and display wait string.
        Returns: (seconds_remaining, status_msg, display_wait)
        """
        is_starting_target = starting and startingAt == self.name.capitalize()
        is_starting_mode = starting
        status_msg = "Pending"
        display_wait = getTimeUnits(seconds_remaining)
        if is_starting_mode:
            if is_starting_target:
                seconds_remaining = 0
                status_msg = "STARTING TARGET"
                display_wait = "NOW"
            else:
                seconds_remaining = 999999999
                status_msg = "Skipped (Start)"
                display_wait = "-"
        elif error_penalty_wait:
            status_msg = "Error Wait"
        elif seconds_remaining == 0:
             status_msg = "Ready"
             display_wait = "NOW"
        return seconds_remaining, status_msg, display_wait

    def _get_effective_last_execution(self) -> Optional[str]:
        lastExec = self.persistence_manager.get_last_execution(self.name)
        if lastExec is None and self.properties.get('waitBeforeFirstRun'):
            lastExec = self.persistence_manager.update_last_execution(self.name, getDatetimeNowStr())
        return lastExec

    def calculate(self, starting: bool, startingAt: str) -> tuple[int, str, str, str, str]:
        last_exec_time = self._get_effective_last_execution()
        seconds_remaining = 0
        timer_details = "Unknown"
        timeoutSeconds = 0
        timeoutSeconds, timer_details, seconds_remaining, error_penalty_wait = self._calculate_error_penalty()
        if not error_penalty_wait:
             timeoutSeconds, timer_details, seconds_remaining = self._calculate_standard_wait(last_exec_time)
        cadency_str = getTimeUnits(timeoutSeconds)
        seconds_remaining, status_msg, display_wait = self._calculate_status_and_display(starting, startingAt, seconds_remaining, error_penalty_wait)
        return seconds_remaining, status_msg, display_wait, timer_details, cadency_str
