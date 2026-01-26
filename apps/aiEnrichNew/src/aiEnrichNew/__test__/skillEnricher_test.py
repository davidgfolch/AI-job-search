from unittest.mock import patch
from ..skillEnricher import skillEnricher, generate_skill_description

@patch('aiEnrichNew.skillEnricher.MysqlUtil')
@patch('aiEnrichNew.skillEnricher.process_skill_enrichment')
@patch('aiEnrichNew.skillEnricher.getEnvBool', return_value=True)
def test_skillEnricher_calls_service(mock_env, mock_process, mock_mysql):
    skillEnricher()
    mock_process.assert_called_once()

@patch('aiEnrichNew.skillEnricher.get_pipeline')
def test_generate_skill_description(mock_pipe):
    mock_pipe.return_value.tokenizer.apply_chat_template.return_value = "Prompt"
    mock_pipe.return_value.return_value = [{'generated_text': 'Desc'}]
    assert generate_skill_description("Skill") == "Desc"
