from unittest.mock import patch, MagicMock
import pytest
import mysql.connector

from commonlib.sql.mysqlUtil import MysqlUtil


class TestMysqlUtil:
    def _create_mock_connection(self):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        return mock_connection, mock_cursor

    def test_initialization_success(self):
        mock_connection = MagicMock()
        assert MysqlUtil(mock_connection).conn == mock_connection

    def test_initialization_connection_error(self):
        assert MysqlUtil().conn is None

    def test_context_manager_enter_exit(self):
        mock_connection = MagicMock()
        with MysqlUtil(mock_connection) as mysql_util:
            assert mysql_util.conn == mock_connection

    def test_context_manager_exit_closes_connection(self):
        mock_connection = MagicMock()
        with MysqlUtil(mock_connection) as mysql_util:
            pass
        mock_connection.close.assert_called_once()
        assert mysql_util.conn is None

    def test_context_manager_exit_no_connection(self):
        MysqlUtil().__exit__(None, None, None)

    def test_get_connection(self):
        mock_connection = MagicMock()
        assert MysqlUtil(mock_connection).getConnection() == mock_connection

    def test_get_connection_no_existing(self):
        with patch('commonlib.sql.mysqlUtil.get_connection', return_value=MagicMock()) as mock_get:
            MysqlUtil().getConnection()
            mock_get.assert_called_once()

    def test_conn_setter(self):
        mock_connection = MagicMock()
        mysql_util = MysqlUtil()
        mysql_util.conn = mock_connection
        assert mysql_util.conn == mock_connection

    def test_execute_query_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        with patch('commonlib.sql.mysqlUtil.getConnection', return_value=mock_connection):
            mysql_util = MysqlUtil(mock_connection)
            mysql_util.executeAndCommit("UPDATE test SET x=%s", (1,))
            assert mock_cursor.execute.called
            assert mock_connection.commit.called

    def test_fetch_one_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchone.return_value = (1, 'test')
        result = MysqlUtil(mock_connection).fetchOne("SELECT * FROM test WHERE id=%s", 1)
        assert result == (1, 'test')

    def test_fetch_all_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchall.return_value = [(1, 'test1'), (2, 'test2')]
        result = MysqlUtil(mock_connection).fetchAll("SELECT * FROM test")
        assert result == [(1, 'test1'), (2, 'test2')]

    def test_count_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchone.return_value = (5,)
        result = MysqlUtil(mock_connection).count("SELECT COUNT(*) FROM test")
        assert result == 5

    def test_insert_job_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 123
        mock_cursor.fetchone.return_value = None
        with patch('commonlib.sql.mysqlUtil.getConnection', return_value=mock_connection):
            job_data = {'job_id': 'test123', 'title': 'Test Job', 'company': 'C', 'url': 'u'}
            result = MysqlUtil(mock_connection).insertJob(job_data)
            assert result == 123

    def test_insert_job_duplicate(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.lastrowid = None
        mock_connection.in_transaction = False
        mock_connection.commit.side_effect = mysql.connector.Error("Duplicate entry")
        job_data = {'job_id': 'test123', 'title': 'Test Job', 'company': 'C', 'url': 'u'}
        result = MysqlUtil(mock_connection).insertJob(job_data)
        assert result is None

    def test_update_from_ai_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.rowcount = 1
        mock_connection.in_transaction = False
        with patch('commonlib.sql.mysqlUtil.getConnection', return_value=mock_connection):
            MysqlUtil(mock_connection).updateFromAI("UPDATE jobs SET salary=%s", ('50000',))
            assert mock_cursor.execute.called

    @pytest.mark.parametrize("scenario,fetch_return,expected", [
        ("Exists", (1, 'job123'), True),
        ("Does not exist", None, False),
    ])
    def test_jobExists(self, scenario, fetch_return, expected):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchone.return_value = fetch_return
        assert MysqlUtil(mock_connection).jobExists('job123') is expected

    def test_getTableDdlColumnNames(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchall.return_value = [
            ('id', 'int', 'NO', 'PRI', None, ''),
            ('jobId', 'varchar(255)', 'YES', '', None, '')
        ]
        with patch('commonlib.sql.query_executor.getColumnTranslated', side_effect=lambda x: x.upper()):
            cols = MysqlUtil(mock_connection).getTableDdlColumnNames('jobs')
            assert cols == ['ID', 'JOBID']

    def test_cursor_context_manager(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        with MysqlUtil(mock_connection).cursor() as cur:
            assert cur is mock_cursor
        mock_cursor.close.assert_called()

    def test_cursor_reconnects_when_not_connected(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_connection.is_connected.return_value = False
        with MysqlUtil(mock_connection).cursor() as cur:
            mock_connection.reconnect.assert_called_once()

    def test_cursor_no_existing_connection(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        with patch('commonlib.sql.mysqlUtil.get_connection', return_value=mock_connection):
            with MysqlUtil().cursor() as cur:
                assert cur is mock_cursor
            mock_connection.close.assert_called()
            assert MysqlUtil().conn is None

    def test_connection_ctx_with_existing(self):
        mock_connection = MagicMock()
        with MysqlUtil(mock_connection).connection_ctx() as conn:
            assert conn is mock_connection

    def test_connection_ctx_without_existing(self):
        mock_connection = MagicMock()
        with patch('commonlib.sql.mysqlUtil.get_connection', return_value=mock_connection):
            with MysqlUtil().connection_ctx() as conn:
                assert conn is mock_connection
            mock_connection.close.assert_called()

    def test_get_scrapper_state(self):
        mysql_util = MysqlUtil(MagicMock())
        with patch.object(mysql_util._scrapper_state_repository, 'get_all', return_value={'site': 'state'}):
            assert mysql_util.get_scrapper_state() == {'site': 'state'}

    def test_update_scrapper_state(self):
        mysql_util = MysqlUtil(MagicMock())
        with patch.object(mysql_util._scrapper_state_repository, 'replace_all') as mock_replace:
            mysql_util.update_scrapper_state({'site': 'new_state'})
            mock_replace.assert_called_once_with({'site': 'new_state'})

    def test_executeAllAndCommit(self):
        mysql_util = MysqlUtil(MagicMock())
        with patch.object(mysql_util._transaction_manager, 'execute_all_and_commit', return_value=[1, 2]):
            assert mysql_util.executeAllAndCommit([{'query': 'q1'}, {'query': 'q2'}]) == [1, 2]

    def test_insert(self):
        mysql_util = MysqlUtil(MagicMock())
        with patch.object(mysql_util._job_repository, 'insert', return_value=123):
            assert mysql_util.insert(('param1',)) == 123
