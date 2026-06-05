import json
from typing import Any

QRY_GET_ALL = "SELECT site, state FROM scrapper_state"
QRY_UPSERT = """
INSERT INTO scrapper_state (site, state) VALUES (%s, %s)
ON DUPLICATE KEY UPDATE state = %s"""
QRY_DELETE = "DELETE FROM scrapper_state WHERE site = %s"
QRY_DELETE_ALL = "DELETE FROM scrapper_state"
QRY_INSERT = "INSERT INTO scrapper_state (site, state) VALUES (%s, %s)"


class ScrapperStateRepository:
    def __init__(self, execute_transaction: callable, execute_query: callable):
        self._execute_transaction = execute_transaction
        self._execute_query = execute_query

    def get_all(self) -> dict[str, Any]:
        rows = self._execute_query(
            lambda c: (c.execute(QRY_GET_ALL), c.fetchall())[1]
        )
        if not rows:
            return {}
        result = {}
        for row in rows:
            state = row[1]
            result[row[0]] = json.loads(state) if isinstance(state, str) else state
        return result

    def upsert(self, site: str, state: dict):
        state_json = json.dumps(state)
        self._execute_transaction(
            lambda c: c.execute(QRY_UPSERT, (site, state_json, state_json))
        )

    def delete(self, site: str):
        self._execute_transaction(
            lambda c: c.execute(QRY_DELETE, [site])
        )

    def replace_all(self, state: dict[str, Any]):
        def op(cursor):
            cursor.execute(QRY_DELETE_ALL)
            for site, site_state in state.items():
                cursor.execute(QRY_INSERT, (site, json.dumps(site_state)))
        self._execute_transaction(op)
