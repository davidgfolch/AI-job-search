import pytest
from ..parsers import parse_skill_enrichment_result


@pytest.mark.parametrize("output, expected_desc_contains, expected_category", [
    pytest.param(
        "**Summary**: Python is a programming language.\n**Deep Technical Details**: Core functionality includes...\n**Category**: Programming Language",
        "Python is a programming language",
        "Programming Language",
        id="with_category",
    ),
    pytest.param(
        "**Summary**: Docker is a containerization platform.\n**Deep Technical Details**: Core functionality includes...\n**Category**: Tool, Platform",
        "Docker is a containerization platform",
        "Tool, Platform",
        id="multiple_categories",
    ),
    pytest.param(
        "**Summary**: Some skill.\n**Deep Technical Details**: Some details.",
        None,
        "Other",
        id="no_category",
    ),
    pytest.param(
        "",
        None,
        "Other",
        id="empty_string",
    ),
    pytest.param(
        '**Summary**: Python.\n**Category**: Language',
        "Python",
        "Language",
        id="newline_before_category",
    ),
])
def test_parse_skill_enrichment_result(output, expected_desc_contains, expected_category):
    description, category = parse_skill_enrichment_result(output)
    if expected_desc_contains:
        assert expected_desc_contains in description
    assert category == expected_category
