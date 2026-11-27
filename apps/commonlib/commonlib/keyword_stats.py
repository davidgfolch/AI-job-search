"""Aggregate scrapper keyword-search events from JSONL logs into per-day statistics.

The scrapper runs on the host and writes one JSON record per line to its own
``data/logs`` directory, rotating at 10 MB (``scrapper.jsonl``, ``scrapper.jsonl.1``,
...). Both the command-line report and the backend API use this module so they report
identical totals, processed counts and already-in-DB duplicates for every
``(scrape date, site, keyword)`` triple.
"""
import glob
import json
import os
import re
from dataclasses import dataclass, field
from typing import Iterator

EVENT_DUPLICATE = "scraper.job.already_exists"
EVENT_LOADED = "scraper.results_loaded"
SUFFIX_TOTAL = ".results_found"
SUFFIX_INSERTED = ".job.inserted"
ROTATION_LIMIT = 6


@dataclass
class KeywordStat:
    date: str
    site: str
    keyword: str
    reported_total: int = 0
    processed: int = 0
    new: int = 0
    duplicates: int = 0
    duplicate_ids: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "date": self.date,
            "site": self.site,
            "keyword": self.keyword,
            "reported_total": self.reported_total,
            "processed": self.processed,
            "new": self.new,
            "duplicates": self.duplicates,
            "duplicate_ids": ",".join(str(job_id) for job_id in self.duplicate_ids),
        }


def log_paths(log_dir: str) -> list:
    """The active log plus its rotated files, oldest suffix last."""
    return sorted(glob.glob(os.path.join(log_dir, "scrapper.jsonl*")))


def has_rotated_history(log_dir: str) -> bool:
    """True when every rotation slot exists, so older days may have aged out."""
    return len(log_paths(log_dir)) >= ROTATION_LIMIT


def _as_int(value) -> int:
    digits = re.sub(r"\D", "", str(value))
    return int(digits) if digits else 0


def _event_date(event: dict) -> str:
    return str(event.get("timestamp", ""))[:10]


def read_events(log_dir: str, start_date: str = None, end_date: str = None) -> Iterator[dict]:
    """Yield well-formed records from the active log and its rotations, newest file first."""
    for path in reversed(log_paths(log_dir)):
        try:
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    try:
                        event = json.loads(line)
                    except (ValueError, TypeError):
                        continue
                    if not isinstance(event, dict):
                        continue
                    day = _event_date(event)
                    if not day or (start_date and day < start_date) or (end_date and day > end_date):
                        continue
                    yield event
        except OSError:
            continue


def aggregate(events: Iterator[dict], max_ids: int = 20, site: str = None, keyword: str = None) -> list:
    """Group keyword events by date/site/keyword; keep the most informative metrics."""
    stats: dict = {}
    seen_ids: dict = {}
    for event in events:
        site_name = event.get("scrapper")
        search = event.get("keyword")
        if not site_name or not search:
            continue
        if site and str(site_name) != site:
            continue
        if keyword and keyword.lower() not in str(search).lower():
            continue
        day = _event_date(event)
        if not day:
            continue
        key = (day, str(site_name), str(search))
        stat = stats.setdefault(key, KeywordStat(day, str(site_name), str(search)))
        name = str(event.get("event", ""))
        if name.endswith(SUFFIX_TOTAL) and "total" in event:
            stat.reported_total = max(stat.reported_total, _as_int(event["total"]))
        elif name == EVENT_LOADED and "loaded" in event:
            stat.processed = max(stat.processed, _as_int(event["loaded"]))
        elif name.endswith(SUFFIX_INSERTED):
            stat.new += 1
        elif name == EVENT_DUPLICATE:
            job_id = event.get("job_id")
            ids = seen_ids.setdefault(key, set())
            if job_id is None or job_id not in ids:
                if job_id is not None:
                    ids.add(job_id)
                stat.duplicates += 1
                if job_id is not None and len(stat.duplicate_ids) < max_ids:
                    stat.duplicate_ids.append(job_id)
    return sorted(stats.values(), key=lambda stat: (stat.date, stat.site, stat.keyword))
