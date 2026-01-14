from unittest.mock import patch, MagicMock
import mysql.connector

from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import emptyToNone, maxLen


class TestMysqlUtil:
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
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        
        with patch('commonlib.mysqlUtil.getConnection', return_value=mock_connection):
            mysql_util = MysqlUtil()
            mysql_util.executeAndCommit("UPDATE test SET x=1", (1, 2))
            
            assert mock_cursor.execute.called
            assert mock_connection.commit.called

    def test_fetch_one_success(self):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 'test')
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        
        mysql_util = MysqlUtil(mock_connection)
        result = mysql_util.fetchOne("SELECT * FROM test WHERE id=%s", 1)
        
        assert result == (1, 'test')
        assert mock_cursor.execute.called
        assert mock_cursor.fetchone.called

    def test_fetch_all_success(self):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 'test1'), (2, 'test2')]
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        
        mysql_util = MysqlUtil(mock_connection)
        result = mysql_util.fetchAll("SELECT * FROM test")
        
        assert result == [(1, 'test1'), (2, 'test2')]
        assert mock_cursor.execute.called
        assert mock_cursor.fetchall.called

    def test_count_success(self):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        
        mysql_util = MysqlUtil(mock_connection)
        result = mysql_util.count("SELECT COUNT(*) FROM test")
        
        assert result == 5

    def test_insert_job_success(self):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 123
        mock_cursor.fetchone.return_value = None  # No existing job
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        
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
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = None
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
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
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        mock_connection.in_transaction = False
        
        with patch('commonlib.mysqlUtil.getConnection', return_value=mock_connection):
            mysql_util = MysqlUtil()
            mysql_util.updateFromAI("UPDATE jobs SET salary=%s WHERE id=%s", ('50000', 1))
            
            assert mock_cursor.execute.called
            assert mock_connection.commit.called


class TestUtilityFunctions:
    def test_empty_to_none_with_empty_string(self):
        result = emptyToNone(('', 'test', None))
        assert result == (None, 'test', None)

    def test_empty_to_none_with_whitespace(self):
        result = emptyToNone(('  ', 'test'))
        assert result == (None, 'test')

    def test_empty_to_none_with_valid_values(self):
        result = emptyToNone(('value1', 'value2'))
        assert result == ('value1', 'value2')

    def test_empty_to_none_with_none_values(self):
        result = emptyToNone((None, None))
        assert result == (None, None)

    def test_max_len_within_limits(self):
        result = maxLen(('short', 'text'), (10, 10))
        assert result == ('short', 'text')

    def test_max_len_exceeds_limits(self):
        result = maxLen(('very long text', 'short'), (6, 10))
        assert result == ('v[...]', 'short')

    def test_max_len_with_none_values(self):
        result = maxLen((None, 'text'), (10, 10))
        assert result == (None, 'text')

    def test_max_len_with_none_limits(self):
        result = maxLen(('text', 'more text'), (None, 6))
        assert result == ('text', 'm[...]')

    def test_max_len_empty_input(self):
        result = maxLen((), ())
        assert result == ()

    def test_max_len_mismatched_lengths(self):
        # Should handle gracefully when lengths don't match (strict=False)
        # With strict=False, zip stops at shortest sequence
        result = maxLen(('text1', 'text2'), (5,))
        assert len(result) == 1  # Only one element processed
        assert result[0] == 'text1'  # 5 chars, limit 5, no truncation