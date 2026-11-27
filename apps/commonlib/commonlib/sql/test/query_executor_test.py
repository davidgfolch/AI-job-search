"Tests for query_executor module."
import pytest
from unittest.mock import MagicMock, patch
from commonlib.sql.query_executor import DEFAULT_SLOW_QUERY_MS, SLOW_QUERY_MAX_CHARS, QueryExecutor, slow_query_threshold_ms


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

    def test_fetch_all_with_columns_uses_the_select_column_names(self, query_executor):
        mock_cursor = MagicMock()
        mock_cursor.column_names = ['id', 'title']
        mock_cursor.fetchall.return_value = [(1, 'Job')]
        with patch.object(query_executor, '_get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(MagicMock(), mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            result = query_executor.fetch_all_with_columns('SELECT id, title FROM jobs')
        assert result == (['id', 'title'], [(1, 'Job')])
        mock_cursor.execute.assert_called_once()

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
            mock_txn.side_effect = lambda cb, query='', operation='': cb(mock_cursor)
            query_executor.update_from_ai('UPDATE jobs SET x=%s', ('val',))
            mock_txn.assert_called_once()

    def test_update_from_ai_no_rows_calls_error(self, query_executor):
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        with patch.object(query_executor, '_execute_transaction') as mock_txn, \
             patch('commonlib.sqlUtil.error') as mock_error:
            mock_txn.side_effect = lambda cb, query='', operation='': cb(mock_cursor)
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

    def test_slow_query_is_logged_with_its_duration(self, query_executor, monkeypatch):
        monkeypatch.setenv('COMMONLIB_DB_SLOW_QUERY_MS', '10')
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        with patch.object(query_executor, '_get_cursor') as mock_get_cursor, \
             patch('commonlib.sql.query_executor.logger') as mock_logger, \
             patch('commonlib.sql.query_executor.time.perf_counter', side_effect=[0.0, 0.050]):
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(MagicMock(), mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            query_executor.fetch_all('SELECT  *\n  FROM jobs')
        mock_logger.warning.assert_called_once_with(
            'db.query_slow', operation='fetch_all', duration_ms=50.0, query='SELECT * FROM jobs')

    def test_fast_query_is_not_logged(self, query_executor, monkeypatch):
        monkeypatch.setenv('COMMONLIB_DB_SLOW_QUERY_MS', '200')
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        with patch.object(query_executor, '_get_cursor') as mock_get_cursor, \
             patch('commonlib.sql.query_executor.logger') as mock_logger, \
             patch('commonlib.sql.query_executor.time.perf_counter', side_effect=[0.0, 0.010]):
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(MagicMock(), mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            query_executor.fetch_all('SELECT 1')
        mock_logger.warning.assert_not_called()

    def test_zero_threshold_disables_the_record(self, query_executor, monkeypatch):
        monkeypatch.setenv('COMMONLIB_DB_SLOW_QUERY_MS', '0')
        with patch('commonlib.sql.query_executor.logger') as mock_logger:
            assert slow_query_threshold_ms() == 0
        mock_logger.warning.assert_not_called()

    def test_threshold_falls_back_when_unset_or_invalid(self, monkeypatch):
        monkeypatch.delenv('COMMONLIB_DB_SLOW_QUERY_MS', raising=False)
        assert slow_query_threshold_ms() == DEFAULT_SLOW_QUERY_MS
        monkeypatch.setenv('COMMONLIB_DB_SLOW_QUERY_MS', 'fast')
        assert slow_query_threshold_ms() == DEFAULT_SLOW_QUERY_MS

    def test_slow_query_is_truncated_to_one_line(self, query_executor, monkeypatch):
        monkeypatch.setenv('COMMONLIB_DB_SLOW_QUERY_MS', '10')
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        long_query = 'SELECT ' + 'x' * 300 + '\nFROM jobs'
        with patch.object(query_executor, '_get_cursor') as mock_get_cursor, \
             patch('commonlib.sql.query_executor.logger') as mock_logger, \
             patch('commonlib.sql.query_executor.time.perf_counter', side_effect=[0.0, 0.030]):
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(MagicMock(), mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            query_executor.fetch_all(long_query)
        query_field = mock_logger.warning.call_args.kwargs['query']
        assert len(query_field) == SLOW_QUERY_MAX_CHARS
        assert '\n' not in query_field

    def test_slow_write_is_logged_from_the_transaction_path(self, query_executor, monkeypatch):
        monkeypatch.setenv('COMMONLIB_DB_SLOW_QUERY_MS', '10')
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        with patch.object(query_executor, '_get_cursor') as mock_get_cursor, \
             patch('commonlib.sql.query_executor.logger') as mock_logger, \
             patch('commonlib.sql.query_executor.time.perf_counter', side_effect=[0.0, 0.020]):
            mock_get_cursor.return_value.__enter__ = MagicMock(return_value=(MagicMock(), mock_cursor))
            mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
            query_executor.update_from_ai('UPDATE jobs SET x=%s', ('v',))
        mock_logger.warning.assert_called_once_with(
            'db.query_slow', operation='update_from_ai', duration_ms=20.0, query='UPDATE jobs SET x=%s')

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
