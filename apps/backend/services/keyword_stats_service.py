import os
from datetime import date
from pathlib import Path
from typing import Optional
from commonlib.keyword_stats import aggregate, has_rotated_history, read_events

DEFAULT_LOG_DIR = Path(__file__).resolve().parents[3] / "apps" / "scrapper" / "data" / "logs"


class KeywordStatsService:
    """Read-only view over the host scrapper's JSONL keyword-search events."""

    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or os.getenv("SCRAPPER_LOG_DIR", str(DEFAULT_LOG_DIR))

    def get_keyword_stats(self, start_date: Optional[str] = None, end_date: Optional[str] = None, site: Optional[str] = None, keyword: Optional[str] = None) -> dict:
        self._validate_date(start_date)
        self._validate_date(end_date)
        rows = aggregate(read_events(self.log_dir, start_date, end_date), site=site, keyword=keyword)
        return {"items": [row.as_dict() for row in rows], "truncated": has_rotated_history(self.log_dir)}

    @staticmethod
    def _validate_date(value: Optional[str]):
        if value:
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"Invalid date '{value}', expected YYYY-MM-DD") from exc
