from unittest.mock import patch, MagicMock
import pytest
import mysql.connector

from commonlib.mysqlUtil import MysqlUtil


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
        mysql_util = MysqlUtil(mock_connection)
        assert mysql_util.conn == mock_connection

    def test_initialization_connection_error(self):
        # MysqlUtil doesn't raise on init, it connects lazily
        mysql_util = MysqlUtil()
        assert mysql_util.conn is None

    def test_context_manager_enter_exit(self):
        mock_connection = MagicMock()
        with MysqlUtil(mock_connection) as mysql_util:
            assert mysql_util.conn == mock_connection

    def test_get_connection(self):
        mock_connection = MagicMock()
        mysql_util = MysqlUtil(mock_connection)
        result = mysql_util.getConnection()
        assert result == mock_connection

    def test_execute_query_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        
        with patch('commonlib.mysqlUtil.getConnection', return_value=mock_connection):
            mysql_util = MysqlUtil()
            mysql_util.executeAndCommit("UPDATE test SET x=1", (1, 2))
            
            assert mock_cursor.execute.called
            assert mock_connection.commit.called

    def test_fetch_one_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchone.return_value = (1, 'test')
        
        mysql_util = MysqlUtil(mock_connection)
        result = mysql_util.fetchOne("SELECT * FROM test WHERE id=%s", 1)
        
        assert result == (1, 'test')
        assert mock_cursor.execute.called
        assert mock_cursor.fetchone.called

    def test_fetch_all_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchall.return_value = [(1, 'test1'), (2, 'test2')]
        
        mysql_util = MysqlUtil(mock_connection)
        result = mysql_util.fetchAll("SELECT * FROM test")
        
        assert result == [(1, 'test1'), (2, 'test2')]
        assert mock_cursor.execute.called
        assert mock_cursor.fetchall.called

    def test_count_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchone.return_value = (5,)
        
        mysql_util = MysqlUtil(mock_connection)
        result = mysql_util.count("SELECT COUNT(*) FROM test")
        
        assert result == 5

    def test_insert_job_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 123
        mock_cursor.fetchone.return_value = None  # No existing job
        
        with patch('commonlib.mysqlUtil.getConnection', return_value=mock_connection):
            mysql_util = MysqlUtil()
            job_data = {
                'job_id': 'test123',
                'title': 'Test Job',
                'company': 'Test Company',
                'url': 'https://test.com/job/1'
            }
            
            result = mysql_util.insertJob(job_data)
            
            assert result == 123

    def test_insert_job_duplicate(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.lastrowid = None
        mock_connection.in_transaction = False
        mock_connection.commit.side_effect = mysql.connector.Error("Duplicate entry")
        
        mysql_util = MysqlUtil(mock_connection)
        job_data = {
            'job_id': 'test123',
            'title': 'Test Job',
            'company': 'Test Company',
            'url': 'https://test.com/job/1'
        }
        
        result = mysql_util.insertJob(job_data)
        
        assert result is None

    def test_update_from_ai_success(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.rowcount = 1
        mock_connection.in_transaction = False
        
        with patch('commonlib.mysqlUtil.getConnection', return_value=mock_connection):
            mysql_util = MysqlUtil()
            mysql_util.updateFromAI("UPDATE jobs SET salary=%s WHERE id=%s", ('50000', 1))
            
            assert mock_cursor.execute.called
            assert mock_connection.commit.called

    @pytest.mark.parametrize("scenario,fetch_return,expected", [
        ("Exists", (1, 'job123'), True),
        ("Does not exist", None, False),
    ])
    def test_jobExists(self, scenario, fetch_return, expected):
        mock_connection, mock_cursor = self._create_mock_connection()
        mock_cursor.fetchone.return_value = fetch_return
        
        mysql_util = MysqlUtil(mock_connection)
        assert mysql_util.jobExists('job123') is expected

    def test_getTableDdlColumnNames(self):
        mock_connection, mock_cursor = self._create_mock_connection()
        
        # Return format of SHOW COLUMNS: Field, Type, Null, Key, Default, Extra
        mock_cursor.fetchall.return_value = [
            ('id', 'int', 'NO', 'PRI', None, ''),
            ('jobId', 'varchar(255)', 'YES', '', None, '')
        ]
        
        mysql_util = MysqlUtil(mock_connection)
        
        with patch('commonlib.mysqlUtil.getColumnTranslated', side_effect=lambda x: x.upper()):
            cols = mysql_util.getTableDdlColumnNames('jobs')
            assert cols == ['ID', 'JOBID']
            assert "SHOW COLUMNS FROM `jobs`" in mock_cursor.execute.call_args[0][0]


