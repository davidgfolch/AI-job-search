import pytest
from unittest.mock import MagicMock
import pandas as pd
from services.statistics_archived_service import StatisticsArchivedService
from repositories.snapshots_repository import SnapshotsRepository
from repositories.statistics_repository import StatisticsRepository


@pytest.fixture
def mock_snapshots_repo():
    return MagicMock(spec=SnapshotsRepository)


@pytest.fixture
def mock_stats_repo():
    return MagicMock(spec=StatisticsRepository)


@pytest.fixture
def service(mock_snapshots_repo, mock_stats_repo):
    return StatisticsArchivedService(
        snapshots_repo=mock_snapshots_repo, stats_repo=mock_stats_repo
    )


def test_get_archived_history_stats(service, mock_snapshots_repo):
    mock_df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "applied": [1],
            "discarded": [0],
            "interview": [0],
        }
    )
    mock_snapshots_repo.get_history_stats_df.return_value = mock_df

    result = service.get_archived_history_stats()

    assert len(result) == 1
    assert result[0]["applied"] == 1


def test_get_snapshots_by_reason(service, mock_snapshots_repo):
    mock_df = pd.DataFrame(
        {"snapshot_reason": ["DELETED", "APPLIED"], "count": [10, 5]}
    )
    mock_snapshots_repo.get_snapshot_count_by_reason.return_value = mock_df

    result = service.get_snapshots_by_reason()

    assert len(result) == 2
