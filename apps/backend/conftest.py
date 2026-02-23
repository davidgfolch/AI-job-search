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


from commonlib.test.db_mock_util import create_mock_db


JOB_COLUMNS = [
    'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
    'web_page', 'created', 'modified'
]


# Export helpers so they can be imported by test modules  
pytest.create_mock_db = create_mock_db
pytest.JOB_COLUMNS = JOB_COLUMNS
