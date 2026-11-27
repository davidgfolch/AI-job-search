import json
import os

import pytest

from commonlib.keyword_stats import aggregate, read_events
from services.scrapper_logs_service import ScrapperLogsService


@pytest.fixture
def log_dir(tmp_path):
    return str(tmp_path)


class TestScrapperLogsService:
    def test_appends_records_into_the_shared_log(self, log_dir):
        records = [
            {"event": "indeed.results_found", "timestamp": "2026-11-19T10:00:00", "scrapper": "Indeed", "keyword": "python", "total": 12},
            {"event": "scraper.job.already_exists", "timestamp": "2026-11-19T10:01:00", "scrapper": "Indeed", "keyword": "python", "job_id": 5},
        ]
        service = ScrapperLogsService(log_dir)
        assert service.append(records) == 2
        rows = aggregate(read_events(log_dir))
        assert rows[0].reported_total == 12
        assert rows[0].duplicates == 1
        assert [json.loads(line)["event"] for line in (tmp_lines(log_dir))] == [row["event"] for row in records]

    def test_skips_invalid_records(self, log_dir):
        service = ScrapperLogsService(log_dir)
        assert service.append([{"event": "ok"}, {"no_event": True}, "bad"]) == 1
        assert len(tmp_lines(log_dir)) == 1

    def test_empty_batch_is_a_no_op(self, log_dir):
        assert ScrapperLogsService(log_dir).append([]) == 0
        assert tmp_lines(log_dir) == []

    def test_validate_app_rejects_foreign_logs(self):
        with pytest.raises(ValueError, match="Only scrapper logs"):
            ScrapperLogsService.validate_app("backend")
        assert ScrapperLogsService.validate_app("scrapper") is None

    def test_default_log_dir_follows_env(self, monkeypatch, log_dir):
        monkeypatch.setenv("SCRAPPER_LOG_DIR", log_dir)
        assert ScrapperLogsService().log_dir == log_dir


def tmp_lines(log_dir):
    path = f"{log_dir}/scrapper.jsonl"
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return handle.read().splitlines()
