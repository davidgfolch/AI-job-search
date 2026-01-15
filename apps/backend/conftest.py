"""Pytest configuration and shared fixtures"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock
from main import app

# Add test directory to Python path to allow imports from test modules
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def client():
    """Shared test client fixture"""
    return TestClient(app)


def create_mock_db(**kwargs):
    """Helper to create a mock database that supports context manager"""
    mock_db = Mock()
    columns = kwargs.get('columns', ['id', 'title', 'company'])
    data_rows = kwargs.get('fetchAll', [])
    
    def fetch_all_side_effect(query, params=None):
        if "SHOW COLUMNS" in str(query).upper():
            return [(c,) for c in columns]
        return data_rows

    mock_db.count.return_value = kwargs.get('count', 0)
    mock_db.fetchAll.side_effect = fetch_all_side_effect
    mock_db.fetchOne.return_value = kwargs.get('fetchOne', None)
    mock_db.getTableDdlColumnNames.return_value = columns
    mock_db.executeAndCommit.return_value = kwargs.get('executeAndCommit', 1)
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=False)
    return mock_db


JOB_COLUMNS = [
    'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
    'web_page', 'created', 'modified', 'merged'
]


# Export helpers so they can be imported by test modules  
pytest.create_mock_db = create_mock_db
pytest.JOB_COLUMNS = JOB_COLUMNS
