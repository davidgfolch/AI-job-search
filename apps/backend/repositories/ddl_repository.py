from typing import Dict, List, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection

class DdlRepository:
    def get_db(self):
        return MysqlUtil(getConnection())

    def get_schema(self) -> Dict[str, List[str]]:
        with self.get_db() as db:
            # simple one-query approach if permissions allow, or iterative
            # Using INFORMATION_SCHEMA is better for one shot
            query = """
                SELECT TABLE_NAME, COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                ORDER BY TABLE_NAME, ORDINAL_POSITION
            """
            rows = db.fetchAll(query)
            schema = {}
            for row in rows:
                table = row[0]
                col = row[1]
                if table not in schema:
                    schema[table] = []
                schema[table].append(col)
            return schema

    def get_keywords(self) -> List[str]:
        # Basic MySQL keywords for autocomplete
        return [
            # Basic Keywords
            "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "LIKE", "IS", "NULL",
            "ORDER BY", "GROUP BY", "HAVING", "LIMIT", "OFFSET", "JOIN", "LEFT", "RIGHT",
            "INNER", "OUTER", "ON", "AS", "DISTINCT", "UNION", "ALL", "EXISTS", "BETWEEN",
            # Logic & Control
            "CASE", "WHEN", "THEN", "ELSE", "END", "TRUE", "FALSE",
            # Aggregation
            "COUNT", "SUM", "AVG", "MAX", "MIN",
            # String Functions
            "CONCAT", "LOWER", "UPPER", "LENGTH", "TRIM", "REPLACE", "SUBSTRING", "COALESCE",
            # Date & Time
            "DATE", "DATE_SUB", "DATE_ADD", "CURDATE", "NOW", "INTERVAL", 
            "DAY", "MONTH", "YEAR", "HOUR", "MINUTE", "SECOND", "CAST", "CONVERT"
        ]
