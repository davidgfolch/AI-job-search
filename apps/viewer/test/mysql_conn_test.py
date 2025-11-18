

def getMysqlConnection():
    """Get MySQL connection using MysqlUtil - Test utility function"""
    from commonlib.mysqlUtil import MysqlUtil
    mysql_util = MysqlUtil()
    return mysql_util.getConnection()


class TestMysqlConn:
    def test_get_mysql_connection_function_exists(self):
        """Test that getMysqlConnection function exists and is callable"""
        assert callable(getMysqlConnection)

    def test_mysql_cached_connection_function_exists(self):
        """Test that mysqlCachedConnection function exists and is callable"""
        from viewer.mysqlConn import mysqlCachedConnection
        assert callable(mysqlCachedConnection)

    def test_mysql_conn_module_imports(self):
        """Test that mysqlConn module can be imported successfully"""
        import viewer.mysqlConn
        assert hasattr(viewer.mysqlConn, 'mysqlCachedConnection')

    def test_get_mysql_connection_uses_mysql_util(self):
        """Test that getMysqlConnection uses MysqlUtil class"""
        import inspect
        source = inspect.getsource(getMysqlConnection)
        assert 'MysqlUtil' in source
        assert 'getConnection' in source