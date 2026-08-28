"Tests for query_executor module."
import pytest
from unittest.mock import MagicMock, patch
from commonlib.sql.query_executor import QueryExecutor


class TestQueryExecutor:
    @pytest.fixture
    def mock_get_connection_ctx(self):
        return MagicMock()

    @pytest.fixture
    def query_executor(self, mock_get_connection_ctx):
        return QueryExecutor(mock_get_connection_ctx)

    def test_init(self, mock_get_connection_ctx):
        executor = QueryExecutor(mock_get_connection_ctx)
        assert executor._get_connection_ctx == mock_get_connection_ctx

    def test_count_returns_result(self, query_executor):
        with patch.object(query_executor, '_execute_query') as mock_execute:
            mock_execute.return_value = 42
            assert query_executor.count('SELECT COUNT(*) FROM jobs') == 42

    def test_fetch_one_returns_row(self, query_executor):
        with patch.object(query_executor, '_execute_query') as mock_execute:
            expected_row = {'id': 1, 'title': 'Job'}
            mock_execute.return_value = expected_row
            assert query_executor.fetch_one('SELECT * FROM jobs WHERE id = %s', 1) == expected_row

    def test_fetch_all_returns_rows(self, query_executor):
        with patch.object(query_executor, '_execute_query') as mock_execute:
            expected_rows = [{'id': 1}, {'id': 2}]
            mock_execute.return_value = expected_rows
            assert query_executor.fetch_all('SELECT * FROM jobs') == expected_rows

    def test_fetch_all_returns_none_on_error(self, query_executor):
        with patch.object(query_executor, '_execute_query') as mock_execute:
            mock_execute.return_value = None
            assert query_executor.fetch_all('SELECT * FROM jobs') is None

    def test_get_table_ddl_column_names_returns_columns(self, query_executor):
        with patch.object(query_executor, 'fetch_all') as mock_fetch:
            mock_fetch.return_value = [('id',), ('title',), ('company',)]
            with patch('commonlib.sql.query_executor.getColumnTranslated') as mock_translate:
                mock_translate.side_effect = lambda x: x
                assert query_executor.get_table_ddl_column_names('jobs') == ['id', 'title', 'company']

    def test_execute_query_raises_exception(self, query_executor):
        with patch.object(query_executor, '_get_cursor') as mock_cursor:
            mock_cursor.side_effect = Exception('DB error')
            with pytest.raises(Exception, match='DB error'):
                query_executor._execute_query(lambda c: c.execute('SELECT 1'))

    def test_update_from_ai_logs_updated(self, query_executor):
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        with patch.object(query_executor, '_execute_transaction') as mock_txn:
            mock_txn.side_effect = lambda cb: cb(mock_cursor)
            query_executor.update_from_ai('UPDATE jobs SET x=%s', ('val',))
            mock_txn.assert_called_once()

    def test_update_from_ai_no_rows_calls_error(self, query_executor):
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        with patch.object(query_executor, '_execute_transaction') as mock_txn, \
             patch('commonlib.sqlUtil.error') as mock_error:
            mock_txn.side_effect = lambda cb: cb(mock_cursor)
            query_executor.update_from_ai('UPDATE jobs SET x=%s', ('val',))
            mock_error.assert_called_once()

    def test_execute_transaction_rollback_on_error(self, query_executor):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("query failed")
        with patch.object(query_executor, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            with pytest.raises(Exception, match="query failed"):
                query_executor._execute_transaction(lambda c: c.execute('SELECT 1'))
            mock_conn.rollback.assert_called_once()

    def test_execute_transaction_commits_on_success(self, query_executor):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        with patch.object(query_executor, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(mock_conn, mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            result = query_executor._execute_transaction(lambda c: 'value')
            assert result == 'value'
            mock_conn.commit.assert_called_once()

    def test_get_cursor_reconnects(self, query_executor):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        query_executor._get_connection_ctx.return_value.__enter__ = MagicMock(return_value=mock_conn)
        query_executor._get_connection_ctx.return_value.__exit__ = MagicMock(return_value=False)
        with query_executor._get_cursor() as (conn, cursor):
            mock_conn.reconnect.assert_called_once()
            assert cursor == mock_cursor
