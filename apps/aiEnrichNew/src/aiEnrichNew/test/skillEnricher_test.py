from unittest.mock import patch, MagicMock
import pytest
from ..skillEnricher import skillEnricher, generate_skill_description

@patch('aiEnrichNew.skillEnricher.MysqlUtil')
@patch('aiEnrichNew.skillEnricher.process_skill_enrichment')
@patch('aiEnrichNew.skillEnricher.getEnvBool', return_value=True)
def test_skillEnricher_calls_service(mock_env, mock_process, mock_mysql):
    skillEnricher()
    mock_process.assert_called_once()

@patch('aiEnrichNew.skillEnricher.get_pipeline')
@pytest.mark.parametrize("llm_output, expected_description, expected_category", [
    ("This is a summary.\n\nCategory: Database", "This is a summary.", "Database"),
    ("**Summary**: Skill info.\n\n**Category**: Framework", "**Summary**: Skill info.", "Framework"),
    ("Detailed info.\n\n## Category: Language", "Detailed info.", "Language"),
    ("Info.\n\ncategory: Tool", "Info.", "Tool"),
    ("Just description without category.", "Just description without category.", "Other"),
    ("Info.\nCategory: **Library**", "Info.", "Library"),
])
def test_generate_skill_description(mock_pipeline, llm_output, expected_description, expected_category):
    mock_generator = MagicMock()
    # Mocking the pipeline return value structure: list of dicts with 'generated_text'
    # We'll use side_effect to return different values for different calls
    mock_pipeline.return_value = mock_generator
    
    # helper to mock the return of the pipeline call
    def mock_return(text):
        return [{'generated_text': text}]

    mock_generator.return_value = mock_return(llm_output)
    assert generate_skill_description("Skill") == (expected_description, expected_category)
