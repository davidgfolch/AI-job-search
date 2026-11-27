import json
import pytest
from services.keyword_stats_service import KeywordStatsService


@pytest.fixture
def log_dir(tmp_path):
    events = [
        {"event": "indeed.results_found", "timestamp": "2026-11-19T10:00:00", "scrapper": "Indeed", "keyword": "python", "total": 12},
        {"event": "scraper.job.already_exists", "timestamp": "2026-11-19T10:01:00", "scrapper": "Indeed", "keyword": "python", "job_id": 5},
    ]
    (tmp_path / "scrapper.jsonl").write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
    return str(tmp_path)


class TestKeywordStatsService:
    def test_aggregates_logs_with_filters(self, log_dir):
        result = KeywordStatsService(log_dir).get_keyword_stats(start_date="2026-11-19", end_date="2026-11-19", site="Indeed", keyword="PYTH")
        assert result["truncated"] is False
        assert result["items"] == [{"date": "2026-11-19", "site": "Indeed", "keyword": "python", "reported_total": 12, "processed": 0, "new": 0, "duplicates": 1, "duplicate_ids": "5"}]

    def test_date_range_excludes_events(self, log_dir):
        result = KeywordStatsService(log_dir).get_keyword_stats(start_date="2026-11-20")
        assert result["items"] == []

    def test_invalid_date_is_rejected(self, log_dir):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            KeywordStatsService(log_dir).get_keyword_stats(start_date="19-11-2026")

    def test_default_log_dir_follows_env(self, monkeypatch, log_dir):
        monkeypatch.setenv("SCRAPPER_LOG_DIR", log_dir)
        assert KeywordStatsService().log_dir == log_dir
