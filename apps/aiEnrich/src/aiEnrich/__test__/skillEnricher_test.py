from unittest.mock import patch, MagicMock
import pytest
from ..skillEnricher import skillEnricher, generate_skill_description

@patch('aiEnrich.skillEnricher.MysqlUtil')
@patch('aiEnrich.skillEnricher.process_skill_enrichment')
@patch('aiEnrich.skillEnricher.getEnvBool', return_value=True)
def test_skillEnricher_calls_service(mock_env, mock_process, mock_mysql):
    skillEnricher()
    mock_process.assert_called_once()

@patch('aiEnrich.skillEnricher.Agent')
@patch('aiEnrich.skillEnricher.Task')
@patch('aiEnrich.skillEnricher.Crew')
@pytest.mark.parametrize("llm_output, expected_description, expected_category", [
    ("This is a summary.\n\nCategory: Database", "This is a summary.", "Database"),
    ("**Summary**: Skill info.\n\n**Category**: Framework", "**Summary**: Skill info.", "Framework"),
    ("Detailed info.\n\n## Category: Language", "Detailed info.", "Language"),
    ("Info.\n\ncategory: Tool", "Info.", "Tool"),
    ("Just description without category.", "Just description without category.", "Other"),
    ("Info.\nCategory: **Library**", "Info.", "Library"),
])
def test_generate_skill_description(mock_crew, mock_task, mock_agent, llm_output, expected_description, expected_category):
    mock_crew.return_value.kickoff.return_value = llm_output
    assert generate_skill_description("Skill") == (expected_description, expected_category)
