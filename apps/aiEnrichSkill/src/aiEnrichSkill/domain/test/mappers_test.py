import pytest
from unittest.mock import patch

from ...config import get_learning_path_system_prompt, get_skill_system_prompt
from ..mappers import build_learning_path_prompt_messages, build_skill_prompt_messages


@pytest.mark.parametrize("context, expect_context", [
    pytest.param("Django, Flask", True, id="with_context"),
    pytest.param("", False, id="no_context"),
])
@patch("aiEnrichSkill.domain.mappers.get_skill_system_prompt")
def test_build_skill_prompt_messages(mock_prompt, context, expect_context):
    mock_prompt.return_value = "System prompt here"

    messages = build_skill_prompt_messages("Python", context)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System prompt here"
    assert messages[1]["role"] == "user"
    assert "Python" in messages[1]["content"]
    if expect_context:
        assert context in messages[1]["content"]
    else:
        assert "Context" not in messages[1]["content"]


@pytest.mark.parametrize("context, expect_context", [
    pytest.param("Django, Flask", True, id="with_context"),
    pytest.param("", False, id="no_context"),
])
@patch("aiEnrichSkill.domain.mappers.get_learning_path_system_prompt")
def test_build_learning_path_prompt_messages(mock_prompt, context, expect_context):
    mock_prompt.return_value = "Learning path system prompt"

    messages = build_learning_path_prompt_messages("Python", context)

    assert len(messages) == 2
    assert messages[0] == {"role": "system", "content": "Learning path system prompt"}
    assert messages[1]["role"] == "user"
    assert "Python" in messages[1]["content"]
    assert "learning path" in messages[1]["content"].lower()
    if expect_context:
        assert context in messages[1]["content"]
    else:
        assert "Context" not in messages[1]["content"]


def test_build_learning_path_prompt_messages_context_optional():
    with patch("aiEnrichSkill.domain.mappers.get_learning_path_system_prompt", return_value="prompt"):
        messages = build_learning_path_prompt_messages("Python")
    assert len(messages) == 2


def test_learning_path_prompt_requires_deep_links_and_docs_first():
    with patch("aiEnrichSkill.config.get_learning_path_max", return_value=3):
        prompt = get_learning_path_system_prompt()
    assert "official documentation" in prompt
    assert "bare homepage" in prompt
    assert "secondary alternative" in prompt
    assert "context line" in prompt


@patch("aiEnrichSkill.config.get_learning_path_max", return_value=3)
@patch("aiEnrichSkill.config.get_skill_categories", return_value="Language")
@patch("aiEnrichSkill.config.get_learning_paths_enabled", return_value=True)
def test_skill_prompt_forbids_generic_homepages(_enabled, _categories, _max):
    prompt = get_skill_system_prompt()
    assert "deep link" in prompt
    assert "bare homepage" in prompt
    assert "secondary to documentation" in prompt
