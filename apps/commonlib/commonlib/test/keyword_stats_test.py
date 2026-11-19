import json

import pytest

from commonlib.keyword_stats import aggregate, has_rotated_history, log_paths, read_events
from commonlib.observability import configure_logging, get_logger, job_log_context, keyword_log_context, log_file_path
from commonlib.test.observability_fixtures import _events, log_dir  # noqa: F401 - fixture registered by import


def _event(event, day="2026-11-19T10:00:00", site="Indeed", keyword="python", **fields):
    return {"event": event, "timestamp": day, "scrapper": site, "keyword": keyword, "level": "info", **fields}


def _write(path, events):
    with open(path, "w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event) + "\n")


class TestAggregate:
    def test_groups_all_metrics_by_date_site_and_keyword(self):
        events = [
            _event("indeed.results_found", total="1.234"),
            _event("indeed.results_found", total="1.200"),
            _event("scraper.results_loaded", loaded=25),
            _event("scraper.results_loaded", loaded=40),
            _event("indeed.job.inserted", job_id=1),
            _event("indeed.job.inserted", job_id=2),
            _event("scraper.job.already_exists", job_id=91),
            _event("scraper.job.already_exists", job_id=92),
            _event("scraper.job.already_exists", job_id=91),
            _event("indeed.results_found", total=7, site="Linkedin", keyword="java"),
        ]
        stats = aggregate(events)
        assert len(stats) == 2
        python, java = stats
        assert (python.date, python.site, python.keyword) == ("2026-11-19", "Indeed", "python")
        assert (python.reported_total, python.processed, python.new, python.duplicates) == (1234, 40, 2, 2)
        assert python.duplicate_ids == [91, 92]
        assert java.reported_total == 7
        assert java.duplicates == 0

    def test_buckets_by_scrape_date_not_insert_date(self):
        events = [
            _event("indeed.results_found", day="2026-11-18T23:59:00", total=3),
            _event("scraper.job.already_exists", day="2026-11-19T00:01:00", job_id=5),
        ]
        stats = aggregate(events)
        assert [(s.date, s.reported_total, s.duplicates) for s in stats] == [("2026-11-18", 3, 0), ("2026-11-19", 0, 1)]

    def test_filters_by_site_and_keyword_substring(self):
        events = [
            _event("indeed.results_found", total=1, site="Indeed", keyword="python remote"),
            _event("linkedin.results_found", total=2, site="Linkedin", keyword="python"),
        ]
        stats = aggregate(events, site="Linkedin", keyword="PYTH")
        assert len(stats) == 1
        assert stats[0].site == "Linkedin"
        assert stats[0].keyword == "python"

    def test_ignores_events_without_attribution(self):
        events = [{"event": "indeed.results_found", "timestamp": "2026-11-19T10:00:00", "total": 9}]
        assert aggregate(events) == []

    def test_caps_duplicate_ids_but_keeps_the_full_count(self):
        events = [_event("scraper.job.already_exists", job_id=i) for i in range(25)]
        stat = aggregate(events, max_ids=3)[0]
        assert stat.duplicates == 25
        assert stat.duplicate_ids == [0, 1, 2]

    def test_as_dict_joins_duplicate_ids(self):
        stat = aggregate([_event("scraper.job.already_exists", job_id=8)], max_ids=2)[0]
        assert stat.as_dict()["duplicate_ids"] == "8"


class TestReadEvents:
    def test_reads_active_and_rotated_files_skipping_bad_lines(self, tmp_path):
        _write(tmp_path / "scrapper.jsonl.1", [_event("indeed.results_found", day="2026-11-17T10:00:00", total=4)])
        _write(tmp_path / "scrapper.jsonl", [_event("scraper.job.already_exists", job_id=3)])
        with open(tmp_path / "scrapper.jsonl", "a", encoding="utf-8") as handle:
            handle.write("{bad json}\n[]\n")
        events = list(read_events(str(tmp_path)))
        assert len(events) == 2
        assert {e["event"] for e in events} == {"indeed.results_found", "scraper.job.already_exists"}

    def test_date_filter_is_inclusive(self, tmp_path):
        _write(tmp_path / "scrapper.jsonl", [
            _event("indeed.results_found", day="2026-11-17T10:00:00"),
            _event("indeed.results_found", day="2026-11-18T10:00:00"),
            _event("indeed.results_found", day="2026-11-19T10:00:00"),
        ])
        events = list(read_events(str(tmp_path), "2026-11-18", "2026-11-19"))
        assert len(events) == 2

    def test_missing_directory_yields_nothing(self, tmp_path):
        assert list(read_events(str(tmp_path / "missing"))) == []
        assert log_paths(str(tmp_path / "missing")) == []

    def test_history_truncation_detected_from_rotation_slots(self, tmp_path):
        assert has_rotated_history(str(tmp_path)) is False
        for index in range(6):
            (tmp_path / f"scrapper.jsonl.{index}").touch()
        assert has_rotated_history(str(tmp_path)) is True


class TestKeywordLogContext:
    def test_binds_site_and_keyword_only_inside_the_block(self, log_dir):
        configure_logging("kw_ctx")
        logger = get_logger("kw_ctx.case")
        with keyword_log_context("Indeed", "python remote"):
            logger.info("indeed.results_found", total=42)
        logger.info("scraper.batch_done")
        first, second = _events(log_file_path("kw_ctx"))
        assert first["scrapper"] == "Indeed"
        assert first["keyword"] == "python remote"
        assert "scrapper" not in second
        assert "keyword" not in second

    def test_explicit_fields_win(self, log_dir):
        configure_logging("kw_ctx_explicit")
        logger = get_logger("kw_ctx_explicit.case")
        with keyword_log_context("Indeed", "python"):
            logger.info("indeed.results_found", keyword="java")
        event = _events(log_file_path("kw_ctx_explicit"))[0]
        assert event["scrapper"] == "Indeed"
        assert event["keyword"] == "java"

    def test_unbinds_after_an_error(self, log_dir):
        configure_logging("kw_ctx_error")
        logger = get_logger("kw_ctx_error.case")
        with pytest.raises(ValueError):
            with keyword_log_context("Linkedin", "python"):
                raise ValueError("boom")
        logger.info("scraper.batch_done")
        assert "keyword" not in _events(log_file_path("kw_ctx_error"))[0]

    def test_nests_with_job_context_without_losing_it(self, log_dir):
        configure_logging("kw_ctx_nested")
        logger = get_logger("kw_ctx_nested.case")
        with keyword_log_context("Indeed", "python"):
            with job_log_context(7):
                logger.info("indeed.job.inserted")
        event = _events(log_file_path("kw_ctx_nested"))[0]
        assert (event["scrapper"], event["keyword"], event["job_id"]) == ("Indeed", "python", 7)
