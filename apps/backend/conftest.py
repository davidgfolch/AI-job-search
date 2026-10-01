"""Pytest configuration and shared fixtures"""
import json
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


def _read_jsonl(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(autouse=True)
def log_records(tmp_path, monkeypatch):
    """Redirect structlog JSONL output to a temp dir and expose a record reader.

    Autouse so a test run never writes into `data/logs`, and so any test can assert on
    the structured records produced by the code under test.
    """
    from commonlib.observability import log_file_path

    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    path = Path(log_file_path())

    def read(event=None, level=None, module=None):
        records = _read_jsonl(path)
        for key, value in (("event", event), ("level", level), ("module", module)):
            if value is not None:
                records = [record for record in records if record.get(key) == value]
        return records

    read.path = path
    return read


from commonlib.test.db_mock_util import create_mock_db


JOB_COLUMNS = [
    'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
    'web_page', 'created', 'modified'
]


# Export helpers so they can be imported by test modules  
pytest.create_mock_db = create_mock_db
pytest.JOB_COLUMNS = JOB_COLUMNS
