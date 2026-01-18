import pytest
from unittest.mock import patch, MagicMock
from services.ddl_service import DdlService

@patch('services.ddl_service.DdlService.get_schema')
@patch('services.ddl_service.DdlService.get_keywords')
def test_get_schema(mock_get_keywords, mock_get_schema, client):
    mock_schema = {"jobs": ["id", "title", "company"], "skills": ["name", "description"]}
    mock_keywords = ["SELECT", "FROM", "WHERE"]
    mock_get_schema.return_value = mock_schema
    mock_get_keywords.return_value = mock_keywords
    response = client.get("/api/ddl/schema")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert "keywords" in data
    assert data["tables"] == mock_schema
    assert data["keywords"] == mock_keywords
