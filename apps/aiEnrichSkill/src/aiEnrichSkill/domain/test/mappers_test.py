import pytest
from unittest.mock import patch

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
