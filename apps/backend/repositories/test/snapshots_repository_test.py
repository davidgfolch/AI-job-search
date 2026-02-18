import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from repositories.snapshots_repository import SnapshotsRepository


@pytest.fixture
def mock_connection():
    with patch("repositories.snapshots_repository.getConnection") as mock:
        yield mock


def test_get_history_stats_df(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "applied": [1],
            "discarded": [0],
            "interview": [0],
        }
    )

    with patch("pandas.read_sql", return_value=mock_df):
        result = repo.get_history_stats_df()

    assert not result.empty


def test_get_snapshot_count_by_reason(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame({"snapshot_reason": ["DELETED"], "count": [10]})

    with patch("pandas.read_sql", return_value=mock_df):
        result = repo.get_snapshot_count_by_reason()

    assert not result.empty
