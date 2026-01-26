import pytest
from unittest.mock import patch, MagicMock
from ..dataExtractor import dataExtractor, extract_job_data, save

def test_extract_job_data():
    pipe = MagicMock()
    pipe.return_value = [{'generated_text': '{"salary": "100k"}'}]
    pipe.tokenizer.apply_chat_template.return_value = "Prompt"
    
    with patch('aiEnrichNew.dataExtractor.rawToJson', return_value={"salary": "100k"}):
        res = extract_job_data(pipe, "Title", "Desc")
        assert res['salary'] == '100k'

@patch('aiEnrichNew.dataExtractor.MysqlUtil')
@patch('aiEnrichNew.dataExtractor.get_pipeline')
def test_dataExtractor_flow(mock_pipe, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql
    mysql.count.return_value = 1
    mysql.fetchAll.return_value = [(1,)]
    mysql.fetchOne.return_value = (1, 'Title', b'Desc', 'Comp')
    
    # pipe mock
    pipe = MagicMock()
    mock_pipe.return_value = pipe
    pipe.return_value = [{'generated_text': 'JSON'}]
    
    with patch('aiEnrichNew.dataExtractor.rawToJson', return_value={}), \
         patch('aiEnrichNew.dataExtractor.mapJob', return_value=('Title', 'Comp', 'Desc')), \
         patch('aiEnrichNew.dataExtractor.save') as mock_save:
         
        dataExtractor()
        mock_save.assert_called()
