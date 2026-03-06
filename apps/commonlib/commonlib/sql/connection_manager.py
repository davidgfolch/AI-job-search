import os
import mysql.connector as mysqlConnector
from mysql.connector import MySQLConnection

DEBUG = False

_conn: MySQLConnection = None


def get_connection(e2e_tests: bool = False) -> MySQLConnection:
    """
    Get MySQL connection from pool.

    Args:
        e2e_tests: If True, connects without database (for E2E test setup)

    Returns:
        MySQL connection instance
    """
    global _conn

    if _conn is None:
        db_host = os.getenv('COMMONLIB_DB_HOST', '127.0.0.1')
        _conn = mysqlConnector.connect(
            host=db_host,
            user='root',
            password='rootPass',
            database=None if e2e_tests else 'jobs',
            pool_name='jobsPool',
            pool_size=20,
        )

    if DEBUG:
        print(_conn.__repr__())

    return mysqlConnector.connect(pool_name='jobsPool')


def getConnection(e2eTests: bool = False) -> MySQLConnection:
    """Backward compatible wrapper for get_connection."""
    return get_connection(e2e_tests=e2eTests)
