from unittest.mock import patch, MagicMock
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
def test_generate_skill_description(mock_crew, mock_task, mock_agent):
    mock_crew.return_value.kickoff.return_value = "Desc"
    # It now returns (description, category), defaulting to "Other" if not found
    assert generate_skill_description("Skill") == ("Desc", "Other")
