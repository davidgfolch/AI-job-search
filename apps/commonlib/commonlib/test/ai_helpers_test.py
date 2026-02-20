import pytest
from unittest.mock import MagicMock, patch
from commonlib.ai_helpers import (
    rawToJson, validateResult, listsToString, fixJsonInvalidAttribute, 
    mapJob, combineTaskResults, footer, LazyDecoder, printJsonException,
    _expand_parenthesized_skills
)
import json

@pytest.mark.parametrize("json_str, expected", [
    ('{"key": "value"}', {"key": "value"}),
    ('```json\n{"key": "value"}\n```', {"key": "value"}),
    ('Here is the json:\n```{"key": "value"}```', {"key": "value"}),
    ('Thought: thinking...\njson object\n{"key": "value"}', {"key": "value"}),
    (r'{"path": "C:\Windows\System32"}', {"path": r"C:\Windows\System32"}),
])
def test_rawToJson_valid_cases(json_str, expected):
    assert rawToJson(json_str) == expected

def test_rawToJson_exception():
    with pytest.raises(json.JSONDecodeError):
        rawToJson("{invalid json}")

def test_fixJsonInvalidAttribute():
    malformed = '{"salary": "100" + "k", "test": "val",",}'
    fixed = fixJsonInvalidAttribute(malformed)
    assert ' + ' in fixed
    assert 'val",' in fixed

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
    # Mock crewOutput
    mock_output = MagicMock()
    mock_output.raw = '{"main": "result"}'
    mock_output.tasks_output = []
    
    res = combineTaskResults(mock_output, debug=False)
    assert res["main"] == "result"

    # With tasks
    task1 = MagicMock()
    task1.raw = '{"salary": "100k"}'
    mock_output.tasks_output = [task1]
    
    res = combineTaskResults(mock_output, debug=True) # cover debug print
    assert res["salary"] == "100k"
    assert res["main"] == "result"

@pytest.mark.parametrize("job_errors, expected_output", [
    (set(), "Processed jobs this run: 1/10"),
    ({"error1"}, "Total job errors: 1"),
])
def test_footer(capsys, job_errors, expected_output):
    footer(10, 0, 100, job_errors)
    captured = capsys.readouterr()
    assert expected_output in captured.out
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
