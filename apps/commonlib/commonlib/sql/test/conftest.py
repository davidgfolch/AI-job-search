"""Shared fixtures for connection_manager tests."""
import os
import queue
from unittest.mock import patch, MagicMock
from mysql.connector.errors import PoolError
import pytest

from commonlib.sql import connection_manager


@pytest.fixture(autouse=True)
def mock_mysql_connect():
    with patch('commonlib.sql.connection_manager.mysqlConnector.connect') as mock_connect, \
         patch.dict(os.environ, {'COMMONLIB_DB_HOST': '127.0.0.1'}, clear=False):
        mock_connect.return_value = MagicMock()
        connection_manager._pool_initialized = False
        yield mock_connect
        connection_manager._pool_initialized = False
