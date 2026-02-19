from unittest.mock import patch, MagicMock
import pytest
from aiEnrichNew.skillEnricher import skillEnricher

@patch("aiEnrichNew.skillEnricher.MysqlUtil")
@patch("aiEnrichNew.skillEnricher.get_pipeline")
@patch("aiEnrichNew.skillEnricher.enrich_skills")
@patch("aiEnrichNew.skillEnricher.getEnvBool", return_value=True)
def test_skillEnricher_calls_service(mock_env, mock_enrich, mock_pipe_fac, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql
    
    pipe = MagicMock()
    mock_pipe_fac.return_value = pipe
    
    start_count = 5
    mock_enrich.return_value = start_count
    
    result = skillEnricher()
    
    assert result == start_count
    mock_enrich.assert_called_once()
    args, _ = mock_enrich.call_args
    assert args[0] == mysql
    assert args[1] == pipe
