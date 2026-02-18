import pytest
from unittest.mock import MagicMock, patch
from repositories.jobQueryRepository import JobQueryRepository


def test_find_applied_by_company():
    repo = JobQueryRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchAll.return_value = [(1,), (2,)]

        result = repo.find_applied_by_company("test")

        assert len(result) == 2
