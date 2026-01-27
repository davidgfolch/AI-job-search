import pytest
from unittest.mock import patch, MagicMock
from ..dataExtractor import dataExtractor, extract_job_data, _save

def test_extract_job_data():
    pipe = MagicMock()
    pipe.return_value = [{'generated_text': '{"salary": "100k"}'}]
    pipe.tokenizer.apply_chat_template.return_value = "Prompt"
    
    with patch('aiEnrichNew.dataExtractor.rawToJson', return_value={"salary": "100k"}):
        res = extract_job_data(pipe, "Title", "Desc")
        assert res['salary'] == '100k'

@patch('aiEnrichNew.dataExtractor.MysqlUtil')
@patch('aiEnrichNew.dataExtractor.get_pipeline')
@patch('aiEnrichNew.dataExtractor.AiEnrichRepository')
def test_dataExtractor_flow(mock_repo_cls, mock_pipe, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql
    
    repo = MagicMock()
    mock_repo_cls.return_value = repo
    repo.count_pending_enrichment.return_value = 1
    repo.get_pending_enrichment_ids.return_value = [1]
    repo.get_job_to_enrich.return_value = (1, 'Title', b'Desc', 'Comp')
    
    # pipe mock
    pipe = MagicMock()
    mock_pipe.return_value = pipe
    pipe.return_value = [{'generated_text': 'JSON'}]
    
    with patch('aiEnrichNew.dataExtractor.rawToJson', return_value={}), \
         patch('aiEnrichNew.dataExtractor.mapJob', return_value=('Title', 'Comp', 'Desc')), \
         patch('aiEnrichNew.dataExtractor._save') as mock_save, \
         patch('aiEnrichNew.dataExtractor._getJobIdsList', return_value=[1]):
         
        dataExtractor()
        mock_save.assert_called()
