"""Tests for transaction_manager module."""
import pytest
from unittest.mock import MagicMock, patch, call
import mysql.connector as mysqlConnector
from commonlib.sql.transaction_manager import TransactionManager


class TestTransactionManager:
    """Tests for TransactionManager class."""

    @pytest.fixture
    def mock_get_connection_ctx(self):
        """Mock get_connection_ctx function."""
        return MagicMock()

    @pytest.fixture
    def transaction_manager(self, mock_get_connection_ctx):
        """Create TransactionManager instance with mock."""
        return TransactionManager(mock_get_connection_ctx)

    def test_init(self, mock_get_connection_ctx):
        """Should initialize with get_connection_ctx function."""
        manager = TransactionManager(mock_get_connection_ctx)
        assert manager._get_connection_ctx == mock_get_connection_ctx

    def test_execute_transaction_commits_on_success(self, transaction_manager, mock_get_connection_ctx):
        """execute_transaction should commit on success."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection_ctx.return_value = mock_conn

        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)

            transaction_manager.execute_transaction(lambda c: 'result')

            mock_conn.commit.assert_called_once()

    def test_execute_transaction_rollback_on_error(self, transaction_manager, mock_get_connection_ctx):
        """execute_transaction should rollback on error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection_ctx.return_value = mock_conn

        with patch.object(transaction_manager, '_rollback') as mock_rollback:
            with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
                db_error = mysqlConnector.Error('DB error')
                mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
                mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
                mock_conn.commit.side_effect = db_error

                transaction_manager.execute_transaction(lambda c: 'result')

                mock_rollback.assert_called_once_with(mock_conn, mock_cursor, db_error)

    def test_execute_query_does_not_commit(self, transaction_manager, mock_get_connection_ctx):
        """execute_query should not commit (read-only)."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection_ctx.return_value = mock_conn

        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            transaction_manager.execute_query(lambda c: 'result')

            mock_conn.commit.assert_not_called()

    def test_execute_and_commit_returns_rowcount(self, transaction_manager):
        """execute_and_commit should return affected row count."""
        with patch.object(transaction_manager, 'execute_transaction') as mock_txn:
            mock_txn.return_value = 5
            result = transaction_manager.execute_and_commit('UPDATE jobs SET title=%s', ('New',))
            assert result == 5

    def test_execute_all_and_commit_returns_row_counts(self, transaction_manager):
        """execute_all_and_commit should return list of row counts."""
        queries = [
            {'query': 'UPDATE jobs SET title=%s', 'params': ('A',)},
            {'query': 'UPDATE jobs SET company=%s', 'params': ('B',)}
        ]
        with patch.object(transaction_manager, 'execute_transaction') as mock_txn:
            mock_txn.return_value = [1, 2]
            result = transaction_manager.execute_all_and_commit(queries)
            assert result == [1, 2]

    def test_rollback_raises_exception(self, transaction_manager, mock_get_connection_ctx):
        """_rollback should re-raise the exception after rollback."""
        mock_conn = MagicMock()
        mock_conn.in_transaction = True
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('status data',)

        test_exception = mysqlConnector.Error('Original error')

        with pytest.raises(mysqlConnector.Error) as exc_info:
            transaction_manager._rollback(mock_conn, mock_cursor, test_exception)

        assert exc_info.value == test_exception
        mock_conn.rollback.assert_called_once()
