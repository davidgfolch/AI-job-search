import os
from pathlib import Path
from typing import Optional

from commonlib.log_writer import append_jsonl, public_record, rotate_if_needed

DEFAULT_LOG_DIR = Path(__file__).resolve().parents[3] / "apps" / "scrapper" / "data" / "logs"
LOG_FILE_NAME = "scrapper.jsonl"


class ScrapperLogsService:
    """Append records shipped by a remote scrapper to the shared JSONL log.

    The file and rotation are the same ones `KeywordStatsService` reads, so shipped
    events show up in the statistics API without a second data path.
    """

    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or os.getenv("SCRAPPER_LOG_DIR", str(DEFAULT_LOG_DIR))

    def append(self, records: list) -> int:
        if not records:
            return 0
        os.makedirs(self.log_dir, exist_ok=True)
        filepath = os.path.join(self.log_dir, LOG_FILE_NAME)
        accepted = 0
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("event"), str):
                continue
            rotate_if_needed(filepath)
            append_jsonl(filepath, public_record(record))
            accepted += 1
        return accepted

    @staticmethod
    def validate_app(app: Optional[str]) -> None:
        if app != "scrapper":
            raise ValueError("Only scrapper logs are accepted")
