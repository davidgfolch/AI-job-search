"""Tests for transaction_manager module."""
import pytest
from unittest.mock import MagicMock, patch, call
import mysql.connector as mysqlConnector
from commonlib.sql.transaction_manager import TransactionManager


class TestTransactionManager:
    @pytest.fixture
    def mock_get_connection_ctx(self):
        return MagicMock()

    @pytest.fixture
    def transaction_manager(self, mock_get_connection_ctx):
        return TransactionManager(mock_get_connection_ctx)

    def test_init(self, mock_get_connection_ctx):
        manager = TransactionManager(mock_get_connection_ctx)
        assert manager._get_connection_ctx == mock_get_connection_ctx

    def test_execute_transaction_commits_on_success(self, transaction_manager, mock_get_connection_ctx):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            transaction_manager.execute_transaction(lambda c: 'result')
            mock_conn.commit.assert_called_once()

    def test_execute_transaction_returns_result(self, transaction_manager):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            result = transaction_manager.execute_transaction(lambda c: 42)
            assert result == 42

    def test_execute_transaction_rollback_on_error(self, transaction_manager, mock_get_connection_ctx):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        with patch.object(transaction_manager, '_rollback') as mock_rollback:
            with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
                db_error = mysqlConnector.Error('DB error')
                mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
                mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
                mock_conn.commit.side_effect = db_error
                transaction_manager.execute_transaction(lambda c: 'result')
                mock_rollback.assert_called_once_with(mock_conn, mock_cursor, db_error)

    def test_execute_query_does_not_commit(self, transaction_manager, mock_get_connection_ctx):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            transaction_manager.execute_query(lambda c: 'result')
            mock_conn.commit.assert_not_called()

    def test_execute_query_returns_result(self, transaction_manager):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            result = transaction_manager.execute_query(lambda c: 'data')
            assert result == 'data'

    def test_execute_query_error_returns_none(self, transaction_manager):
        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(side_effect=mysqlConnector.Error("fail"))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            result = transaction_manager.execute_query(lambda c: 'data')
            assert result is None

    def test_execute_and_commit_returns_rowcount(self, transaction_manager):
        with patch.object(transaction_manager, 'execute_transaction') as mock_txn:
            mock_txn.return_value = 5
            result = transaction_manager.execute_and_commit('UPDATE jobs SET title=%s', ('New',))
            assert result == 5

    def test_execute_all_and_commit_returns_row_counts(self, transaction_manager):
        queries = [
            {'query': 'UPDATE jobs SET title=%s', 'params': ('A',)},
            {'query': 'UPDATE jobs SET company=%s', 'params': ('B',)}
        ]
        with patch.object(transaction_manager, 'execute_transaction') as mock_txn:
            mock_txn.return_value = [1, 2]
            result = transaction_manager.execute_all_and_commit(queries)
            assert result == [1, 2]

    def test_execute_all_and_commit_runs_op(self, transaction_manager):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = [None, None]
        mock_cursor.rowcount = 3
        queries = [
            {'query': 'UPDATE jobs SET title=%s', 'params': ('A',)},
            {'query': 'UPDATE jobs SET company=%s', 'params': ('B',)}
        ]
        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            result = transaction_manager.execute_all_and_commit(queries)
            assert result == [3, 3]
            mock_conn.commit.assert_called_once()
            assert mock_cursor.execute.call_count == 2

    def test_execute_and_commit_runs_callback(self, transaction_manager):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.return_value = None
        mock_cursor.rowcount = 7
        with patch.object(transaction_manager, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            result = transaction_manager.execute_and_commit('UPDATE jobs SET title=%s', ('X',))
            assert result == 7
            mock_conn.commit.assert_called_once()

    def test_rollback_in_transaction(self, transaction_manager):
        mock_conn = MagicMock()
        mock_conn.in_transaction = True
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('status data',)
        test_exception = mysqlConnector.Error('Original error')
        with pytest.raises(mysqlConnector.Error) as exc_info:
            transaction_manager._rollback(mock_conn, mock_cursor, test_exception)
        assert exc_info.value == test_exception
        mock_conn.rollback.assert_called_once()

    def test_rollback_not_in_transaction(self, transaction_manager):
        mock_conn = MagicMock()
        mock_conn.in_transaction = False
        mock_cursor = MagicMock()
        test_exception = mysqlConnector.Error('Original error')
        with pytest.raises(mysqlConnector.Error):
            transaction_manager._rollback(mock_conn, mock_cursor, test_exception)
        mock_conn.rollback.assert_not_called()

    def test_rollback_error_during_rollback(self, transaction_manager):
        mock_conn = MagicMock()
        mock_conn.in_transaction = True
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = mysqlConnector.Error("rollback fail")
        test_exception = mysqlConnector.Error('Original error')
        with pytest.raises(mysqlConnector.Error) as exc_info:
            transaction_manager._rollback(mock_conn, mock_cursor, test_exception)
        assert exc_info.value == test_exception

    def test_get_cursor_reconnects_when_not_connected(self, transaction_manager):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        transaction_manager._get_connection_ctx.return_value.__enter__ = MagicMock(return_value=mock_conn)
        transaction_manager._get_connection_ctx.return_value.__exit__ = MagicMock(return_value=False)
        with transaction_manager._get_cursor() as (conn, cursor):
            mock_conn.reconnect.assert_called_once()
            assert cursor == mock_cursor

    def test_get_cursor_sets_isolation_level(self, transaction_manager):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        transaction_manager._get_connection_ctx.return_value.__enter__ = MagicMock(return_value=mock_conn)
        transaction_manager._get_connection_ctx.return_value.__exit__ = MagicMock(return_value=False)
        with transaction_manager._get_cursor() as (conn, cursor):
            mock_cursor.execute.assert_called_with('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
