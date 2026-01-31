
import pytest
from unittest.mock import patch, MagicMock
from repositories.jobs_repository import JobsRepository
from commonlib.db_mock_util import create_mock_db

@patch('repositories.jobs_repository.MysqlUtil')
@patch('repositories.jobs_repository.getConnection')
def test_update_jobs_by_filter_uses_return_value(mock_get_conn, mock_mysql_util_cls):
    """
    Verify that update_jobs_by_filter returns the result of executeAndCommit
    instead of trying to access db.cursor.rowcount.
    """
    # Setup
    mock_db_instance = create_mock_db(executeAndCommit=42)
    mock_mysql_util_cls.return_value = mock_db_instance
    
    expected_rowcount = 42
    
    # Ensure accessing db.cursor.rowcount would trigger the AttributeError if the code was still buggy
    # Ideally, we don't even define rowcount on the cursor mock if we want to simulate strictness,
    # but since db.cursor is a method on the real class, accessing db.cursor.rowcount 
    # on the mock might depend on how Mock handles it. 
    # The real error is accessing attribute 'rowcount' on a function/method 'cursor'.
    # On a MagicMock, accessing .cursor gives another MagicMock. accessing .rowcount on that gives another MagicMock.
    # So the buggy code wouldn't crash with a default MagicMock.
    # We can explicitly make db.cursor fail if accessed as an attribute with .rowcount?
    # Actually, the best verification is checking the return value is what we set for executeAndCommit.
    
    repo = JobsRepository()
    
    update_data = {'ignored': True}
    where_clauses = ["1=1"]
    params = []
    
    # Act
    result = repo.update_jobs_by_filter(where_clauses, params, update_data)
    
    # Assert
    mock_db_instance.executeAndCommit.assert_called_once()
    assert result == expected_rowcount
