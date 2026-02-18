import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from repositories.combinedStatsRepository import CombinedStatsRepository


def test_get_combined_history_stats_df():
    repo = CombinedStatsRepository()
    mock_df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "applied": [1],
            "discarded": [0],
            "interview": [0],
        }
    )

    with patch("repositories.combinedStatsRepository.getConnection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        with patch("pandas.read_sql", return_value=mock_df):
            result = repo.get_combined_history_stats_df()

    assert not result.empty
