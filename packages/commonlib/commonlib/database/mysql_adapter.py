from typing import List, Optional, Sequence
import mysql.connector as mysqlConnector
from ..interfaces.database_interface import DatabaseInterface

class MySQLAdapter(DatabaseInterface):
    def __init__(self, connection: mysqlConnector.MySQLConnection):
        self.connection = connection

    def executeQuery(self, query: str, params: Optional[Sequence] = None) -> List[tuple]:
        with self._getCursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def executeSingle(self, query: str, params: Optional[Sequence] = None) -> Optional[tuple]:
        with self._getCursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def executeCount(self, query: str, params: Optional[Sequence] = None) -> int:
        result = self.executeSingle(query, params)
        return result[0] if result else 0

    def executeCommit(self, query: str, params: Optional[Sequence] = None) -> int:
        with self._getCursor() as cursor:
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.rowcount

    def _getCursor(self):
        if not self.connection.is_connected():
            self.connection.reconnect()
        cursor = self.connection.cursor()
        cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
        return cursor