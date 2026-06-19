import pytest
from unittest.mock import patch

from ..mappers import build_skill_prompt_messages


@pytest.mark.parametrize("context, expect_context", [
    pytest.param("Django, Flask", True, id="with_context"),
    pytest.param("", False, id="no_context"),
])
@patch("aiEnrichSkill.domain.mappers.get_skill_system_prompt")
@patch("aiEnrichSkill.domain.mappers.get_input_max_len")
def test_build_skill_prompt_messages(mock_max_len, mock_prompt, context, expect_context):
    mock_prompt.return_value = "System prompt here"
    mock_max_len.return_value = 12000

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
