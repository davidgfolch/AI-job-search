from typing import Dict, List, Any
import re
from commonlib.mysqlUtil import MysqlUtil, getConnection


class DdlRepository:
    def get_db(self):
        return MysqlUtil(getConnection())

    def get_enum_values(self, table_name: str, column_name: str) -> List[str]:
        with self.get_db() as db:
            query = """
                SELECT COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = %s 
                  AND COLUMN_NAME = %s
            """
            rows = db.fetchAll(query, [table_name, column_name])
            if not rows or not rows[0]:
                return []
            column_type = rows[0][0]
            if not column_type or not column_type.startswith("enum("):
                return []
            enum_content = column_type[5:-1]
            values = re.findall(r"'([^']+)'", enum_content)
            return values

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
