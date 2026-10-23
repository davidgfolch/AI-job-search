from structlog.testing import capture_logs
import pytest
from unittest.mock import MagicMock, patch
from commonlib.ai_helpers import validateResult, listsToString, mapJob, combineTaskResults, footer, printJob, logIdleWait, idleWait, _expand_parenthesized_skills, flatten_skill_groups, _normalizeModality
from commonlib.terminalColor import cyan
from commonlib.test.ai_helpers_fixtures import (
    LISTS_TO_STRING_CASES, LISTS_TO_STRING_TYPES_CASES, FLATTEN_STRING_CASES, FLATTEN_LIST_CASES, SALARY_CASES, CV_MATCH_CASES, MAP_JOB_CASES,
    MODALITY_CASES, EXPAND_CASES, FOOTER_ERROR_CASES, FOOTER_JOB_ELAPSED_CASES, LOG_IDLE_TERMINAL_CASES, completed,
)

@pytest.mark.parametrize("value, expected", LISTS_TO_STRING_CASES)
def test_listsToString(value, expected):
    data = {"tech": value}
    listsToString(data, ["tech"])
    assert data["tech"] == expected

@pytest.mark.parametrize("data, expected", LISTS_TO_STRING_TYPES_CASES)
def test_listsToString_types(data, expected):
    listsToString(data, list(data))
    assert data == expected

@pytest.mark.parametrize("value, expected", FLATTEN_STRING_CASES)
def test_flatten_skill_groups_string(value, expected):
    assert flatten_skill_groups(value) == expected

@pytest.mark.parametrize("value, expected", FLATTEN_LIST_CASES)
def test_flatten_skill_groups_list(value, expected):
    assert flatten_skill_groups(value) == expected

@pytest.mark.parametrize("value", [123, None])
def test_flatten_skill_groups_invalid_type(value):
    assert flatten_skill_groups(value) == []

@pytest.mark.parametrize("input_data, expected_salary", SALARY_CASES)
def test_validateResult_salary(input_data, expected_salary):
    validateResult(input_data)
    assert input_data["salary"] == expected_salary

@pytest.mark.parametrize("input_data, expected_cv_match", CV_MATCH_CASES)
def test_validateResult_cv_match(input_data, expected_cv_match):
    validateResult(input_data)
    assert input_data["cv_match_percentage"] == expected_cv_match

@pytest.mark.parametrize("markdown, expected_markdown", MAP_JOB_CASES)
def test_mapJob(markdown, expected_markdown):
    title, company, markdown = mapJob((1, "Title", markdown, "Company"))
    assert (title, company, markdown) == ("Title", "Company", expected_markdown)

def test_combineTaskResults():
    mock_output = MagicMock()
    mock_output.raw = '{"main": "result"}'
    mock_output.tasks_output = []
    assert combineTaskResults(mock_output, debug=False)["main"] == "result"
    task = MagicMock()
    task.raw = '{"salary": "100k"}'
    mock_output.tasks_output = [task]
    res = combineTaskResults(mock_output, debug=True)  # cover debug print
    assert res["salary"] == "100k"
    assert res["main"] == "result"

def test_combineTaskResults_task_overrides_null_modality():
    """Task result should override None values from main output (the modality bug fix)."""
    mock_output = MagicMock()
    mock_output.raw = '{"salary": null, "modality": null}'
    task = MagicMock()
    task.raw = '{"modality": "REMOTE", "salary": "50k"}'
    mock_output.tasks_output = [task]
    res = combineTaskResults(mock_output, debug=False)
    assert res["modality"] == "REMOTE"
    assert res["salary"] == "50k"

@pytest.mark.parametrize("input_modality, expected", MODALITY_CASES)
def test_normalizeModality(input_modality, expected):
    result = {"modality": input_modality}
    _normalizeModality(result)
    assert result["modality"] == expected

@pytest.mark.parametrize("value, expected", [("remote", ["REMOTE"]), ("ONSITE", None), (["REMOTE", "hybrid"], ["REMOTE", "HYBRID"])])
def test_validateResult_normalizes_modality(value, expected):
    result = {"modality": value}
    validateResult(result)
    assert result["modality"] == expected

@pytest.mark.parametrize("value, expected", EXPAND_CASES)
def test__expand_parenthesized_skills(value, expected):
    assert _expand_parenthesized_skills(value) == expected

@pytest.mark.parametrize("job_errors, expected_errors", FOOTER_ERROR_CASES)
def test_footer(job_errors, expected_errors):
    with capture_logs() as records:
        footer(10, 0, 100, job_errors)
    c = completed(records)
    assert (c["processed"], c["total"], c["total_processed"], c["job_errors"]) == (1, 10, 100, expected_errors)
    assert "elapsed" not in c

def test_footer_total_never_below_processed(capsys):
    with capture_logs() as records: footer(1, 11, 12, set())
    printJob("enrich", 1, 11, 589064, "T", "C", 100)
    assert (c := completed(records))["total"] == c["processed"] == 12 and "job 12/12" in capsys.readouterr().out

@pytest.mark.parametrize("elapsed, present, absent", [
    (None, ["Processed jobs this run: 1449/5653", "total processed jobs: 1449", "Total job errors: 0"], ["Time elapsed"]),
    (3600.0, ["Processed jobs this run: 1449/5653", "Time elapsed:", "/job)", "elapsed"], []),
])
def test_footer_progress_line(elapsed, present, absent):
    """The n/m line is the human half of the record; without it a container shows only fields."""
    kwargs = {"elapsed_time": elapsed} if elapsed else {}
    with capture_logs() as records:
        footer(5653, 1448, 1449, set(), **kwargs)
    c = completed(records)
    assert all(s in c["console"] or s in c for s in present)
    assert all(s not in c["console"] for s in absent)
    assert ("elapsed" in c) is (elapsed is not None)

@pytest.mark.parametrize("config, present, absent", [
    ("JVM Spring", "Config: JVM Spring", None),
    (None, None, "Config:"),
])
def test_footer_config(config, present, absent):
    kwargs = {"config": config} if config else {}
    with capture_logs() as records:
        footer(10, 0, 1, set(), **kwargs)
    c = completed(records)
    assert c.get("config") == config if config else "config" not in c
    assert (present in c["console"]) if present else (absent not in c["console"])

@pytest.mark.parametrize("elapsed_time, console_suffix, batch_fields", FOOTER_JOB_ELAPSED_CASES)
def test_footer_job_elapsed(elapsed_time, console_suffix, batch_fields):
    """`Time elapsed` reports the job just finished; the media stays a batch average."""
    with capture_logs() as records:
        footer(146, 40, 41, set(), elapsed_time=elapsed_time, job_elapsed=41.0)
    c = completed(records)
    assert console_suffix in c["console"]
    assert c["job_elapsed"] == "41s"
    if batch_fields is None:
        assert "Media" not in c["console"] and "elapsed" not in c
    else:
        for key, value in batch_fields.items():
            assert c[key] == value

class TestLogIdleWait:
    def test_docker_logs_one_record_then_waits(self):
        with patch("commonlib.ai_helpers.isDocker", return_value=True), \
             patch("commonlib.ai_helpers.WakeableTimer") as mock_timer, \
             patch("commonlib.ai_helpers.consoleTimer") as mock_console_timer, \
             capture_logs() as records:
            logIdleWait("All jobs enriched.", "10s", "jobs.skipped", reason="no_pending_jobs")
        assert len(records) == 1
        assert records[0]["event"] == "jobs.skipped"
        assert records[0]["message"] == "All jobs enriched."
        assert "console" not in records[0]
        assert records[0]["wait_seconds"] == 10
        assert records[0]["reason"] == "no_pending_jobs"
        mock_timer.return_value.wait.assert_called_once_with(10)
        mock_console_timer.assert_not_called()

    def test_docker_strips_color_from_the_message(self):
        with patch("commonlib.ai_helpers.isDocker", return_value=True), \
             patch("commonlib.ai_helpers.WakeableTimer"), \
             capture_logs() as records:
            logIdleWait(cyan("All jobs enriched."), "10s", "jobs.skipped", reason="no_pending_jobs")
        assert records[0]["message"] == "All jobs enriched."
        assert "\x1b" not in records[0]["message"]

    def test_docker_does_not_emit_a_separate_timer_event(self):
        with patch("commonlib.ai_helpers.isDocker", return_value=True), \
             patch("commonlib.ai_helpers.WakeableTimer"), \
             capture_logs() as records:
            logIdleWait("Backend unavailable", "10s", "ai.retry_wait", reason="backend_unavailable")
        assert [r["event"] for r in records] == ["ai.retry_wait"]

    @pytest.mark.parametrize("event, reason", LOG_IDLE_TERMINAL_CASES)
    def test_terminal_keeps_the_countdown_and_logs_nothing(self, event, reason):
        with patch("commonlib.ai_helpers.isDocker", return_value=False), \
             patch("commonlib.ai_helpers.consoleTimer") as mock_timer, \
             patch("commonlib.ai_helpers.WakeableTimer") as mock_wake, \
             capture_logs() as records:
            logIdleWait("All jobs enriched.", "10s", event, reason=reason)
        mock_timer.assert_called_once_with("All jobs enriched.", "10s")
        mock_wake.assert_not_called()
        assert records == []

class TestIdleWait:
    def test_docker_waits_without_logging(self):
        """The service already logged the cycle, so the wait adds no second line."""
        with patch("commonlib.ai_helpers.isDocker", return_value=True), \
             patch("commonlib.ai_helpers.WakeableTimer") as mock_timer, \
             capture_logs() as records:
            idleWait("All skills enriched.", "10s")
        assert records == []
        mock_timer.return_value.wait.assert_called_once_with(10)

    def test_terminal_keeps_the_countdown_without_logging(self):
        with patch("commonlib.ai_helpers.isDocker", return_value=False), \
             patch("commonlib.ai_helpers.consoleTimer") as mock_timer, \
             capture_logs() as records:
            idleWait("All skills enriched.", "10s")
        mock_timer.assert_called_once_with("All skills enriched.", "10s")
        assert records == []
