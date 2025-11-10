import pytest
from unittest.mock import patch, MagicMock


def buildWhereClause(filters):
    """Build WHERE clause from filters dictionary"""
    if not filters:
        return ""
    
    conditions = []
    for key, value in filters.items():
        if value is not None:
            conditions.append(f"{key} = %s")
    
    if not conditions:
        return ""
    
    return "WHERE " + " AND ".join(conditions)


def buildSelectQuery(table, columns, filters=None):
    """Build SELECT query with optional WHERE clause"""
    column_list = ", ".join(columns) if columns else ""
    query = f"SELECT {column_list} FROM {table}"
    
    where_clause = buildWhereClause(filters)
    if where_clause:
        query += " " + where_clause
    
    return query


class TestSqlUtil:
    def test_build_where_clause_empty_filters(self):
        result = buildWhereClause({})
        assert result == ""

    def test_build_where_clause_none_filters(self):
        result = buildWhereClause(None)
        assert result == ""

    def test_build_where_clause_single_filter(self):
        filters = {'name': 'John'}
        result = buildWhereClause(filters)
        assert result == "WHERE name = %s"

    def test_build_where_clause_multiple_filters(self):
        filters = {'name': 'John', 'age': 30, 'city': 'New York'}
        result = buildWhereClause(filters)
        
        # Should contain WHERE and all conditions with AND
        assert result.startswith("WHERE ")
        assert "name = %s" in result
        assert "age = %s" in result
        assert "city = %s" in result
        assert " AND " in result

    def test_build_where_clause_with_none_values(self):
        filters = {'name': 'John', 'age': None, 'city': 'New York'}
        result = buildWhereClause(filters)
        
        # Should only include non-None values
        assert "name = %s" in result
        assert "city = %s" in result
        assert "age" not in result

    def test_build_where_clause_with_empty_string_values(self):
        filters = {'name': 'John', 'description': '', 'city': 'New York'}
        result = buildWhereClause(filters)
        
        # Should include empty strings as they are valid values
        assert "name = %s" in result
        assert "description = %s" in result
        assert "city = %s" in result

    def test_build_where_clause_special_characters(self):
        filters = {'name': "O'Connor", 'description': 'Test & Development'}
        result = buildWhereClause(filters)
        
        # Should handle special characters properly
        assert "name = %s" in result
        assert "description = %s" in result

    def test_build_select_query_basic(self):
        result = buildSelectQuery("users", ["id", "name"])
        assert result == "SELECT id, name FROM users"

    def test_build_select_query_with_where(self):
        filters = {'active': True}
        result = buildSelectQuery("users", ["id", "name"], filters)
        
        assert result.startswith("SELECT id, name FROM users")
        assert "WHERE active = %s" in result

    def test_build_select_query_all_columns(self):
        result = buildSelectQuery("users", ["*"])
        assert result == "SELECT * FROM users"

    def test_build_select_query_single_column(self):
        result = buildSelectQuery("users", ["name"])
        assert result == "SELECT name FROM users"

    def test_build_select_query_multiple_columns(self):
        columns = ["id", "name", "email", "created_at"]
        result = buildSelectQuery("users", columns)
        assert result == "SELECT id, name, email, created_at FROM users"

    def test_build_select_query_with_complex_filters(self):
        filters = {'status': 'active', 'role': 'admin', 'department': 'IT'}
        result = buildSelectQuery("employees", ["id", "name"], filters)
        
        assert result.startswith("SELECT id, name FROM employees")
        assert "WHERE " in result
        assert "status = %s" in result
        assert "role = %s" in result
        assert "department = %s" in result

    def test_build_select_query_empty_columns(self):
        result = buildSelectQuery("users", [])
        assert result == "SELECT  FROM users"

    def test_build_select_query_table_with_schema(self):
        result = buildSelectQuery("schema.users", ["id", "name"])
        assert result == "SELECT id, name FROM schema.users"

    def test_build_where_clause_order_consistency(self):
        # Test that the order of conditions is consistent
        filters = {'z_field': 'value1', 'a_field': 'value2', 'm_field': 'value3'}
        result1 = buildWhereClause(filters)
        result2 = buildWhereClause(filters)
        
        # Results should be identical (assuming consistent ordering)
        assert result1 == result2

    def test_build_where_clause_boolean_values(self):
        filters = {'active': True, 'deleted': False}
        result = buildWhereClause(filters)
        
        assert "active = %s" in result
        assert "deleted = %s" in result

    def test_build_where_clause_numeric_values(self):
        filters = {'age': 25, 'salary': 50000.50, 'count': 0}
        result = buildWhereClause(filters)
        
        assert "age = %s" in result
        assert "salary = %s" in result
        assert "count = %s" in result

    def test_build_select_query_with_empty_filters(self):
        result = buildSelectQuery("users", ["id", "name"], {})
        assert result == "SELECT id, name FROM users"

    def test_build_select_query_with_none_filters(self):
        result = buildSelectQuery("users", ["id", "name"], None)
        assert result == "SELECT id, name FROM users"