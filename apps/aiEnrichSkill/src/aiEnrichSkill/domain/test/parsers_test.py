import pytest
from ..parsers import parse_learning_path_result, parse_skill_enrichment_result


@pytest.mark.parametrize("output, expected_desc_contains, expected_category, expected_links", [
    pytest.param(
        "**Summary**: Python is a programming language.\n**Deep Technical Details**: Core functionality includes...\n**Category**: Programming Language",
        "Python is a programming language", "Programming Language", [], id="with_category"),
    pytest.param(
        "**Summary**: Docker is a containerization platform.\n**Deep Technical Details**: Core functionality includes...\n**Category**: Tool, Platform",
        "Docker is a containerization platform", "Tool, Platform", [], id="multiple_categories"),
    pytest.param(
        "**Summary**: Some skill.\n**Deep Technical Details**: Some details.",
        None, "Other", [], id="no_category"),
    pytest.param("", None, "Other", [], id="empty_string"),
    pytest.param(
        '**Summary**: Python.\n**Category**: Language',
        "Python", "Language", [], id="newline_before_category"),
    pytest.param(
        "**Summary**: Python.\n**Category**: Language\n**Learning Path**:\n- https://docs.python.org/3/\n- https://realpython.com/",
        "Python", "Language", ["https://docs.python.org/3/", "https://realpython.com/"], id="with_learning_path"),
])
def test_parse_skill_enrichment_result(output, expected_desc_contains, expected_category, expected_links):
    description, category, links = parse_skill_enrichment_result(output)
    if expected_desc_contains:
        assert expected_desc_contains in description
    assert category == expected_category
    assert links == expected_links


def test_parse_skill_enrichment_result_strips_wrapping_quotes():
    description, category, links = parse_skill_enrichment_result('"**Summary**: Java.\n**Category**: Language"')
    assert "Java" in description
    assert category == "Language"
    assert links == []


@pytest.mark.parametrize("output, expected", [
    pytest.param("Learning Path:\n- https://docs.python.org/\n- https://realpython.com/", ["https://docs.python.org/", "https://realpython.com/"], id="section"),
    pytest.param("'Learning Path:\n- https://docs.python.org/'", ["https://docs.python.org/"], id="quoted"),
    pytest.param("https://docs.python.org/", ["https://docs.python.org/"], id="bare_url"),
    pytest.param("No links at all.", [], id="no_links"),
])
def test_parse_learning_path_result(output, expected):
    assert parse_learning_path_result(output) == expected
