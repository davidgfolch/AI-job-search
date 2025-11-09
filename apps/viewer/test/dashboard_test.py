import pytest
from unittest.mock import patch, MagicMock

def test_dashboard_module_exists():
    """Test that dashboard module can be imported"""
    try:
        import viewer.dashboard
        assert hasattr(viewer.dashboard, 'stats')
    except ImportError:
        pytest.fail("Dashboard module could not be imported")

@patch('viewer.statistics.createdByDate.run')
@patch('viewer.statistics.createdByHours.run')
@patch('viewer.statistics.appliedDiscardedByDateStats.run')
@patch('viewer.dashboard.st')
@patch('commonlib.mysqlUtil.MysqlUtil')
def test_stats_function_exists(mock_mysql_util, mock_st, mock_applied_stats, mock_hours, mock_date, mock_mysql: MagicMock):
    """Test that stats function exists and can be called"""
    from viewer.dashboard import stats
    
    # Mock streamlit components
    mock_st.markdown = MagicMock()
    
    # Mock MysqlUtil
    mock_util_instance = MagicMock()
    mock_util_instance.fetchAll.return_value = [('10 Applied',), ('5 Interviews',)]
    mock_mysql_util.return_value = mock_util_instance
    
    # Call the function
    stats()
    
    # Verify the statistics modules were called
    mock_date.assert_called_once()
    mock_hours.assert_called_once()
    mock_applied_stats.assert_called_once()
