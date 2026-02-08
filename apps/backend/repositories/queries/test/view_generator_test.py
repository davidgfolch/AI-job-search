from repositories.queries.view_generator import generate_config_view_sql, drop_config_view_sql

def test_generate_config_view_sql():
    """Test generating SQL for config view"""
    sql, name = generate_config_view_sql(100, {'search': 'foo'})
    assert name == "config_view_100"
    assert "CREATE OR REPLACE VIEW config_view_100" in sql
    assert "LIKE " in sql
    assert "'%foo%'" in sql

def test_drop_config_view_sql():
    """Test generating SQL for dropping config view"""
    sql = drop_config_view_sql(200)
    assert sql == "DROP VIEW IF EXISTS config_view_200"

def test_generate_config_view_sql_with_all_filters():
    """Test generating SQL with all supported filters including sql_filter, status, etc."""
    filters = {
        'search': 'dev',
        'sql_filter': "salary > 100",
        'status': 'interview',
        'not_status': 'discarded'
    }
    sql, name = generate_config_view_sql(300, filters)
    
    # These assertions verify if the filters are present in the generated SQL
    assert "salary > 100" in sql
    assert "`interview` = 1" in sql
    assert "`discarded` = 0" in sql

def test_generate_config_view_sql_with_flat_boolean_filters():
    """Test generating SQL with boolean filters at the top level"""
    filters = {
        'flagged': True,
        'seen': 'false',
        'search': 'test'
    }
    sql, name = generate_config_view_sql(400, filters)
    
    assert "`flagged` = 1" in sql
    assert "`seen` = 0" in sql
    assert "'%test%'" in sql
    assert "FROM jobs" in sql
    assert "FROM jobs j" not in sql

