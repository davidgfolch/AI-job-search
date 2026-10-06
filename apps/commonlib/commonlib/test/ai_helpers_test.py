from structlog.testing import capture_logs

import pytest
from unittest.mock import MagicMock, patch
from commonlib.ai_helpers import (
    validateResult, listsToString, mapJob, combineTaskResults, footer, logIdleWait, idleWait,
    _expand_parenthesized_skills, flatten_skill_groups, _normalizeModality, VALID_MODALITIES
)
from commonlib.terminalColor import cyan
import json



@pytest.mark.parametrize("value, expected", [
    ("Java (Spring, Hibernate)", "Java,Spring,Hibernate"),
    ("React (Hooks, Context), Node.js (Express)", "React,Hooks,Context,Node.js,Express"),
    ("Cloud (AWS (EC2, S3), Azure)", "Cloud,AWS,EC2,S3,Azure"),
    ("No parentheses here", "No parentheses here"),
    ("JS (React.js, Vue.js, Node-RED)", "JS,React.js,Vue.js,Node-RED"),
    ("C# (.NET Core, ASP.NET)", "C#,.NET Core,ASP.NET"),
    ("C# (.NET Core,, ASP.NET, ,  ASP.NET)", "C#,.NET Core,ASP.NET"),
    ("None specified", None),
    ("null", None),
    ("Null", None),
])
def test_listsToString(value, expected):
    data = {"tech": value}
    listsToString(data, ["tech"])
    assert data["tech"] == expected

def test_listsToString_types():
    data = {"req": ["a", "b"], "opt": "c, d", "none": None}
    listsToString(data, ["req", "opt", "none"])
    assert data["req"] == "a,b"
    assert data["opt"] == "c,d"
    assert data["none"] is None

def test_listsToString_list_with_parenthesized_groups():
    data = {"tech": ["Java", "AWS (RDS, Cognito, ECS)", "Observability (Grafana, Sentry)"]}
    listsToString(data, ["tech"])
    assert data["tech"] == "Java,AWS,RDS,Cognito,ECS,Observability,Grafana,Sentry"

@pytest.mark.parametrize("value, expected", [
    ("Java,Spring Boot,AWS (RDS, Cognito, ECS),Observability (Grafana, Sentry)",
     ["Java", "Spring Boot", "AWS", "RDS", "Cognito", "ECS", "Observability", "Grafana", "Sentry"]),
    ("Cloud (AWS (EC2, S3), Azure)", ["Cloud", "AWS", "EC2", "S3", "Azure"]),
    ("No parentheses here", ["No parentheses here"]),
    ("Java,Java,AWS (EC2, S3)", ["Java", "AWS", "EC2", "S3"]),
])
def test_flatten_skill_groups_string(value, expected):
    assert flatten_skill_groups(value) == expected

@pytest.mark.parametrize("value, expected", [
    (["AWS (RDS, Cognito)", "Java", "Observability (Grafana, Sentry)"],
     ["AWS", "RDS", "Cognito", "Java", "Observability", "Grafana", "Sentry"]),
    (["Cloud (AWS (EC2, S3), Azure)", "Java"], ["Cloud", "AWS", "EC2", "S3", "Azure", "Java"]),
    (["Java", None, "AWS (EC2, S3)", "AWS (EC2, S3)"], ["Java", "AWS", "EC2", "S3"]),
    ([], []),
])
def test_flatten_skill_groups_list(value, expected):
    assert flatten_skill_groups(value) == expected

def test_flatten_skill_groups_invalid_type():
    assert flatten_skill_groups(123) == []
    assert flatten_skill_groups(None) == []


@pytest.mark.parametrize("input_data, expected_salary", [
    ({"salary": "Competitive String with no numbers"}, None),
    ({"salary": "50k-60k"}, "50k-60k"),
    ({"salary": {"min": 50, "max": 60}}, "50-60"),
    ({"salary": {"amount": 70}}, "70"),
    ({"salary": {"other": "value"}}, None),
    ({"salary": "Sueldo: 50k"}, "50k"),
])
def test_validateResult_salary(input_data, expected_salary):
    validateResult(input_data)
    assert input_data["salary"] == expected_salary

@pytest.mark.parametrize("input_data, expected_cv_match", [
    ({"cv_match_percentage": "85"}, "85"),
    ({"cv_match_percentage": "105"}, None),
    ({"cv_match_percentage": "high"}, None),
])
def test_validateResult_cv_match(input_data, expected_cv_match):
    validateResult(input_data)
    assert input_data["cv_match_percentage"] == expected_cv_match

@pytest.mark.parametrize("markdown, expected_markdown", [
    (b"Markdown", "Markdown\n"),
    ("MarkdownStr", "MarkdownStr\n"),
])
def test_mapJob(markdown, expected_markdown):
    job = (1, "Title", markdown, "Company")
    title, company, markdown = mapJob(job)
    assert title == "Title"
    assert company == "Company"
    assert markdown == expected_markdown

def test_combineTaskResults():
    mock_output = MagicMock()
    mock_output.raw = '{"main": "result"}'
    mock_output.tasks_output = []
    assert combineTaskResults(mock_output, debug=False)["main"] == "result"

    task1 = MagicMock()
    task1.raw = '{"salary": "100k"}'
    mock_output.tasks_output = [task1]
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

@pytest.mark.parametrize("input_modality, expected", [
    ("REMOTE", "REMOTE"),
    ("remote", "REMOTE"),
    ("Hybrid", "HYBRID"),
    ("ON_SITE", "ON_SITE"),
    ("invalid", None),
    (None, None),
    ("", None),
])
def test_normalizeModality(input_modality, expected):
    result = {"modality": input_modality}
    _normalizeModality(result)
    assert result["modality"] == expected

def test_validateResult_normalizes_modality():
    result = {"modality": "remote"}
    validateResult(result)
    assert result["modality"] == "REMOTE"

def test_validateResult_clears_invalid_modality():
    result = {"modality": "ONSITE"}  # missing underscore - invalid
    validateResult(result)
    assert result["modality"] is None


@pytest.mark.parametrize("value, expected", [
    ("Java (Spring, Hibernate)", "Java, Spring, Hibernate"),
    ("React (Hooks, Context), Node.js (Express)", "React, Hooks, Context, Node.js, Express"),
    ("Cloud (AWS (EC2, S3), Azure)", "Cloud, AWS, EC2, S3, Azure"),
    ("No parentheses here", "No parentheses here"),
    ("JS (React.js, Vue.js, Node-RED)", "JS, React.js, Vue.js, Node-RED"),
    ("C# (.NET Core, ASP.NET)", "C#, .NET Core, ASP.NET"),
    ("C# (.NET Core,, ASP.NET, ,  ASP.NET)", "C#, .NET Core, ASP.NET, ASP.NET"),
])
def test__expand_parenthesized_skills(value, expected):
    assert _expand_parenthesized_skills(value) == expected


def _completed(records):
    return [r for r in records if r["event"] == "ai.batch_completed"][0]


@pytest.mark.parametrize("job_errors, expected_errors", [
    (set(), 0),
    ({"error1"}, 1),
])
def test_footer(job_errors, expected_errors):
    with capture_logs() as records:
        footer(10, 0, 100, job_errors)

    completed = _completed(records)
    assert completed["processed"] == 1
    assert completed["total"] == 10
    assert completed["total_processed"] == 100
    assert completed["job_errors"] == expected_errors
    assert "elapsed" not in completed


def test_footer_includes_elapsed():
    with capture_logs() as records:
        footer(10, 0, 100, set(), elapsed_time=12.0)

    completed = _completed(records)
    assert "elapsed" in completed
    assert "elapsed_per_job" in completed


def test_footer_prints_the_progress_line():
    """The n/m line is the human half of the record; without it a container shows only fields."""
    with capture_logs() as records:
        footer(5653, 1448, 1449, set())

    console = _completed(records)["console"]
    assert "Processed jobs this run: 1449/5653" in console
    assert "total processed jobs: 1449" in console
    assert "Total job errors: 0" in console
    assert "Time elapsed" not in console


def test_footer_progress_line_includes_elapsed():
    with capture_logs() as records:
        footer(5653, 1448, 1449, set(), elapsed_time=3600.0)

    console = _completed(records)["console"]
    assert "Processed jobs this run: 1449/5653" in console
    assert "Time elapsed:" in console
    assert "/job)" in console


@pytest.mark.parametrize("elapsed_time, console_suffix, batch_fields", [
    (1668.0, "Time elapsed: 41s (Media: 40s/job)", {"elapsed": "27m 48s", "elapsed_per_job": "40s"}),
    (None, "Time elapsed: 41s", None),
])
def test_footer_job_elapsed(elapsed_time, console_suffix, batch_fields):
    """`Time elapsed` reports the job just finished; the media stays a batch average."""
    with capture_logs() as records:
        footer(146, 40, 41, set(), elapsed_time=elapsed_time, job_elapsed=41.0)

    completed = _completed(records)
    assert console_suffix in completed["console"]
    assert completed["job_elapsed"] == "41s"
    if batch_fields is None:
        assert "Media" not in completed["console"]
        assert "elapsed" not in completed
    else:
        for key, value in batch_fields.items():
            assert completed[key] == value


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

    @pytest.mark.parametrize("event, reason", [
        pytest.param("jobs.skipped", "no_pending_jobs", id="no_pending_jobs"),
        pytest.param("ai.retry_wait", "backend_unavailable", id="backend_unavailable"),
        pytest.param("jobs.skipped", "no_pending_skills", id="no_pending_skills"),
    ])
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
