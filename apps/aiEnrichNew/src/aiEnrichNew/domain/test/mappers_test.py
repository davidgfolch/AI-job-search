import pytest
from unittest.mock import patch
from ..mappers import map_db_job_to_domain, build_job_prompt_messages


@patch("aiEnrichNew.domain.mappers.mapJob")
def test_map_db_job_to_domain(mock_mapJob):
    mock_mapJob.return_value = ("Title", "Company", "Markdown content")
    job_row = (1, "other", "data")

    result = map_db_job_to_domain(job_row)

    assert result['id'] == 1
    assert result['title'] == "Title"
    assert result['company'] == "Company"
    assert result['markdown'] == "Markdown content"
    assert result['length'] == 16
    mock_mapJob.assert_called_with(job_row)


@pytest.mark.parametrize("max_len, markdown_len, expect_truncated", [
    pytest.param(100, 50, False, id="no_truncation"),
    pytest.param(10, 20, True, id="truncated"),
])
@patch("aiEnrichNew.domain.mappers.get_job_system_prompt")
@patch("aiEnrichNew.domain.mappers.get_input_max_len")
def test_build_job_prompt_messages(mock_max_len, mock_sys_prompt, max_len, markdown_len, expect_truncated):
    mock_max_len.return_value = max_len
    mock_sys_prompt.return_value = "System Prompt"

    job = {
        'title': "Job Title",
        'markdown': "A" * markdown_len
    }

    messages = build_job_prompt_messages(job)

    assert len(messages) == 2
    assert messages[0]['role'] == 'system'
    assert messages[0]['content'] == "System Prompt"
    assert messages[1]['role'] == 'user'
    assert "Job Title" in messages[1]['content']
    if expect_truncated:
        assert "A" * markdown_len not in messages[1]['content']
    else:
        assert "A" * markdown_len in messages[1]['content']
