import pytest
from unittest.mock import patch, MagicMock
from services.ddl_service import DdlService

@patch('services.ddl_service.DdlRepository')
def test_get_schema(mock_repo_class):
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_schema = {"jobs": ["id", "title"], "skills": ["name"]}
    mock_repo.get_schema.return_value = mock_schema
    service = DdlService()
    result = service.get_schema()
    assert result == mock_schema
    mock_repo.get_schema.assert_called_once()

@patch('services.ddl_service.DdlRepository')
def test_get_keywords(mock_repo_class):
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_keywords = ["SELECT", "FROM", "WHERE"]
    mock_repo.get_keywords.return_value = mock_keywords
    service = DdlService()
    result = service.get_keywords()
    assert result == mock_keywords
    mock_repo.get_keywords.assert_called_once()
