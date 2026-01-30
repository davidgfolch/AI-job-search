import pytest
from unittest.mock import patch, MagicMock
from repositories.ddl_repository import DdlRepository

@patch('repositories.ddl_repository.MysqlUtil')
@patch('repositories.ddl_repository.getConnection')
def test_get_schema(mock_get_connection, mock_mysql_util):
    mock_db = MagicMock()
    mock_mysql_util.return_value.__enter__.return_value = mock_db
    mock_db.fetchAll.return_value = [
        ('jobs', 'id'), ('jobs', 'title'), ('skills', 'name')
    ]
    repo = DdlRepository()
    result = repo.get_schema()
    assert 'jobs' in result
    assert 'skills' in result
    assert 'id' in result['jobs']
    assert 'title' in result['jobs']
    assert 'name' in result['skills']

def test_get_keywords():
    repo = DdlRepository()
    keywords = repo.get_keywords()
    assert isinstance(keywords, list)
    assert 'SELECT' in keywords
    assert 'FROM' in keywords
    assert 'WHERE' in keywords
    assert len(keywords) > 0
