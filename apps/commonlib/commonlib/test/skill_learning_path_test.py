import json
import pytest

from commonlib.skill_learning_path import (
    SOURCE_DUCKDUCKGO, SOURCE_LLM, SOURCE_MANUAL, SOURCE_UNKNOWN, LearningPathLink,
    dedupe_urls, deserialize_learning_path, learning_path_as_dicts,
    parse_learning_path_urls, parse_skill_llm_output, serialize_learning_path, split_learning_path_section,
)


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


@pytest.mark.parametrize("raw, expected", [
    pytest.param(None, [], id="none"),
    pytest.param([], [], id="empty"),
    pytest.param(["https://docs.python.org/3/"], [LearningPathLink("https://docs.python.org/3/", SOURCE_UNKNOWN)], id="legacy_strings"),
    pytest.param('["https://docs.python.org/3/"]', [LearningPathLink("https://docs.python.org/3/", SOURCE_UNKNOWN)], id="legacy_json_string"),
    pytest.param([{"url": "https://docs.python.org/3/", "source": "llm"}], [LearningPathLink("https://docs.python.org/3/", SOURCE_LLM)], id="tagged_objects"),
    pytest.param([LearningPathLink("https://x.dev", SOURCE_DUCKDUCKGO)], [LearningPathLink("https://x.dev", SOURCE_DUCKDUCKGO)], id="namedtuples"),
    pytest.param([{"url": " https://x.dev ", "source": "MANUAL"}], [LearningPathLink("https://x.dev", SOURCE_MANUAL)], id="normalizes_case_and_spaces"),
    pytest.param([{"url": "https://x.dev", "source": "made_up"}], [LearningPathLink("https://x.dev", SOURCE_UNKNOWN)], id="unknown_source_coerced"),
    pytest.param([{"url": ""}, "", {"source": "llm"}], [], id="empty_items_dropped"),
    pytest.param("not-json", [], id="malformed_json"),
    pytest.param({"url": "https://x.dev"}, [], id="non_list"),
])
def test_deserialize_learning_path(raw, expected):
    assert deserialize_learning_path(raw) == expected


@pytest.mark.parametrize("links, expected", [
    pytest.param([], None, id="empty_returns_none"),
    pytest.param(None, None, id="none_returns_none"),
    pytest.param(["https://x.dev"], '[{"url": "https://x.dev", "source": "unknown"}]', id="legacy_strings_tagged_unknown"),
    pytest.param([LearningPathLink("https://x.dev", SOURCE_LLM)], '[{"url": "https://x.dev", "source": "llm"}]', id="tagged_link"),
    pytest.param([{"url": "https://x.dev", "source": "duckduckgo"}], '[{"url": "https://x.dev", "source": "duckduckgo"}]', id="tagged_dict"),
])
def test_serialize_learning_path(links, expected):
    assert serialize_learning_path(links) == expected
    if expected is not None:
        assert json.loads(expected) == learning_path_as_dicts(links)
