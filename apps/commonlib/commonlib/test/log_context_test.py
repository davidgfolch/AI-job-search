import pytest

from commonlib.log_context import job_log_context, keyword_log_context
from commonlib.observability import configure_logging, get_logger, log_file_path
from commonlib.test.observability_fixtures import _events, log_dir  # noqa: F401 - the fixtures register by being imported here


class TestJobLogContext:
    def test_binds_job_id_only_inside_the_block(self, log_dir):
        configure_logging("ctx_bind")
        logger = get_logger("ctx_bind.case")
        with job_log_context(582714):
            logger.info("job.result", duration=1.0)
        logger.info("jobs.skipped", wait_seconds=10)
        records = _events(log_file_path("ctx_bind"))
        assert records[0]["job_id"] == 582714
        assert "job_id" not in records[1]

    def test_explicit_job_id_wins(self, log_dir):
        configure_logging("ctx_explicit")
        logger = get_logger("ctx_explicit.case")
        with job_log_context(582714):
            logger.info("job.retry", job_id=42)
        assert _events(log_file_path("ctx_explicit"))[0]["job_id"] == 42

    def test_none_job_id_does_not_bind(self, log_dir):
        configure_logging("ctx_none")
        logger = get_logger("ctx_none.case")
        with job_log_context(None):
            logger.info("job.not_found")
        assert "job_id" not in _events(log_file_path("ctx_none"))[0]

    def test_job_id_is_unbound_after_an_error(self, log_dir):
        configure_logging("ctx_error")
        logger = get_logger("ctx_error.case")
        with pytest.raises(ValueError):
            with job_log_context(7):
                raise ValueError("boom")
        logger.info("job.critical_error")
        assert "job_id" not in _events(log_file_path("ctx_error"))[0]

    def test_nested_blocks_inherit_the_inner_id(self, log_dir):
        configure_logging("ctx_nested")
        logger = get_logger("ctx_nested.case")
        with job_log_context(1):
            with job_log_context(2):
                logger.info("job.result")
        assert _events(log_file_path("ctx_nested"))[0]["job_id"] == 2


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
