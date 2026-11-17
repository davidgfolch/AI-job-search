import pytest

from commonlib.skill_learning_path import dedupe_urls, parse_learning_path_urls, parse_skill_llm_output, split_learning_path_section


@pytest.mark.parametrize("text, expected_body", [
    pytest.param(
        "**Summary**: Python.\n**Learning Path**:\n- https://docs.python.org/\n**Category**: Language",
        "- https://docs.python.org/\n", id="bold_header_with_trailing_category"),
    pytest.param(
        "Learning Path:\n- https://roadmap.sh/python\n- https://roadmap.sh/python/", "- https://roadmap.sh/python\n- https://roadmap.sh/python/", id="plain_header_to_end"),
    pytest.param(
        "**Summary**: No links here.\n**Category**: Other", "", id="no_section"),
])
def test_split_learning_path_section(text, expected_body):
    cleaned, body = split_learning_path_section(text)
    assert body == expected_body
    assert "Learning Path:" not in cleaned if expected_body else cleaned == text


def test_split_learning_path_section_removes_section_from_text():
    cleaned, body = split_learning_path_section(
        "**Summary**: Docker.\n**Learning Path**:\n- https://docs.docker.com/\n**Category**: Tool"
    )
    assert "https://" not in cleaned
    assert "Summary" in cleaned
    assert "https://docs.docker.com/" in body


@pytest.mark.parametrize("header", [
    "Learning Path:",
    "**Learning Path**:",
    "## Learning Path",
    "1. Learning Path:",
    "- **Learning Path**:",
], ids=["plain", "bold", "heading", "numbered", "bullet"])
def test_parse_learning_path_urls_accepts_header_variants(header):
    text = f"{header}\n- https://docs.python.org/3/\n- https://realpython.com/"
    assert parse_learning_path_urls(text) == ["https://docs.python.org/3/", "https://realpython.com/"]


def test_parse_learning_path_urls_falls_back_to_any_url_without_header():
    assert parse_learning_path_urls("Python docs: https://docs.python.org/3/") == ["https://docs.python.org/3/"]


def test_parse_learning_path_urls_ignores_urls_outside_section():
    text = "See https://example.com for context.\n**Learning Path**:\n- https://docs.python.org/"
    assert parse_learning_path_urls(text) == ["https://docs.python.org/"]


@pytest.mark.parametrize("urls, expected", [
    pytest.param(
        ["https://docs.python.org/3/", "https://docs.python.org/3"],
        ["https://docs.python.org/3/"], id="trailing_slash_dedupe"),
    pytest.param(
        ["https://Docs.Python.org/3/", "https://docs.python.org/3/"],
        ["https://Docs.Python.org/3/"], id="case_insensitive_dedupe"),
    pytest.param(
        ["https://docs.python.org/3/.", "https://realpython.com/)"],
        ["https://docs.python.org/3/", "https://realpython.com/"], id="trailing_punctuation"),
    pytest.param(["", "  "], [], id="blanks"),
])
def test_dedupe_urls(urls, expected):
    assert dedupe_urls(urls) == expected


@pytest.mark.parametrize("output, expected_desc, expected_category, expected_links", [
    ("**Summary**: Python is a language.\n**Category**: Programming Language", "Python is a language", "Programming Language", []),
    ("Category: Cloud Platform\n\n**Summary**: GCP is a cloud platform.", "GCP is a cloud platform", "Cloud Platform", []),
    ("Just a description without category", "Just a description without category", "Other", []),
    ("", "", "Other", []),
    ("## Category: Framework\nDesc here", "Desc here", "Framework", []),
    ("**Category**: `DevOps`\nSome description", "Some description", "DevOps", []),
    ("**Summary**: Python.\n**Category**: Language\n**Learning Path**:\n- https://docs.python.org/3/\n- https://www.freecodecamp.org/", "Python", "Language", ["https://docs.python.org/3/", "https://www.freecodecamp.org/"]),
])
def test_parse_skill_llm_output(output, expected_desc, expected_category, expected_links):
    desc, category, links = parse_skill_llm_output(output)
    assert expected_desc in desc
    assert category == expected_category
    assert links == expected_links


def test_parse_skill_llm_output_strips_links_from_description():
    desc, category, links = parse_skill_llm_output("**Summary**: Python is a language.\n**Learning Path**:\n- https://docs.python.org/\n**Category**: Language")
    assert "https://" not in desc
    assert category == "Language"
    assert links == ["https://docs.python.org/"]


def test_parse_skill_llm_output_learning_path_only():
    desc, category, links = parse_skill_llm_output("Learning Path:\n- https://roadmap.sh/python\n- https://roadmap.sh/python/\n- https://roadmap.sh/python#intro")
    assert desc == ""
    assert category == "Other"
    assert links == ["https://roadmap.sh/python", "https://roadmap.sh/python#intro"]
