from typing import List, Optional, Sequence
import mysql.connector as mysqlConnector
from ..interfaces.database_interface import DatabaseInterface

class MySQLAdapter(DatabaseInterface):
    """MySQL implementation of DatabaseInterface"""
    
    def __init__(self, connection: mysqlConnector.MySQLConnection):
        self.connection = connection
    
    def execute_query(self, query: str, params: Optional[Sequence] = None) -> List[tuple]:
        with self._get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    def execute_single(self, query: str, params: Optional[Sequence] = None) -> Optional[tuple]:
        with self._get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    
    def execute_count(self, query: str, params: Optional[Sequence] = None) -> int:
        result = self.execute_single(query, params)
        return result[0] if result else 0
    
    def execute_commit(self, query: str, params: Optional[Sequence] = None) -> int:
        with self._get_cursor() as cursor:
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.rowcount
    
    def _get_cursor(self):
        if not self.connection.is_connected():
            self.connection.reconnect()
        cursor = self.connection.cursor()
        cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
        return cursor