import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import pytest
import pandas as pd

# Add paths for imports
current_dir = Path(__file__).parent
viewer_dir = current_dir.parent
sys.path.insert(0, str(viewer_dir))

# Mock streamlit before importing viewer modules
mock_streamlit = MagicMock()
mock_streamlit.session_state = {}
sys.modules['streamlit'] = mock_streamlit

import viewer.viewAndEditHelper as vah
from viewer.viewAndEditConstants import (
    FF_KEY_WHERE, FF_KEY_SEARCH, FF_KEY_SALARY, FF_KEY_DAYS_OLD,
    FF_KEY_BOOL_FIELDS, FF_KEY_BOOL_NOT_FIELDS,
    FF_KEY_SINGLE_SELECT, FF_KEY_LIST_HEIGHT, 
    FF_KEY_PRESELECTED_ROWS, DEFAULT_ORDER, LIST_HEIGHT)


class TestGetJobListQuery:
    """Test the getJobListQuery function"""

    def test_get_job_list_query_default(self, monkeypatch):
        """Test building query with default filters"""
        def mock_get_state(key, default=None):
            return default
        
        def mock_get_state_bool(key):
            return False
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'getStateBool', mock_get_state_bool)
        
        # Ensure we have a concrete template for formatting
        monkeypatch.setattr(vah, 'QRY_SELECT_JOBS_VIEWER', "{selectFields} WHERE {where} ORDER BY {order}", raising=False)
        query = str(vah.getJobListQuery())

        assert 'where' in query.lower()
        assert '1=1' in query
        assert DEFAULT_ORDER in query

    def test_get_job_list_query_with_where_filter(self, monkeypatch):
        """Test query with custom WHERE filter"""
        custom_filter = "salary > 50000"
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_WHERE:
                return custom_filter
            return default
        
        def mock_get_state_bool(key):
            return key == FF_KEY_WHERE
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'getStateBool', mock_get_state_bool)
        
        monkeypatch.setattr(vah, 'QRY_SELECT_JOBS_VIEWER', "{selectFields} WHERE {where} ORDER BY {order}", raising=False)
        query = str(vah.getJobListQuery())

        assert custom_filter in query

    def test_get_job_list_query_with_search_filter(self, monkeypatch):
        """Test query with search filter"""
        search_term = "Python,Django"
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_SEARCH:
                return search_term
            # Check for boolean key name for search filter
            if key == 'searchFilter_bool':
                return True
            return default
        
        def mock_get_state_bool(key):
            if key == FF_KEY_SEARCH:
                return True
            return False
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'getStateBool', mock_get_state_bool)
        monkeypatch.setattr(vah, 'getBoolKeyName', lambda k: f'{k}_bool')
        
        monkeypatch.setattr(vah, 'QRY_SELECT_JOBS_VIEWER', "{selectFields} WHERE {where} ORDER BY {order}", raising=False)
        query = str(vah.getJobListQuery())

        # Query should contain search-related filters
        assert 'and' in query or 'Python' in query.lower() or 'django' in query.lower()

    def test_get_job_list_query_with_days_old_filter(self, monkeypatch):
        """Test query with days old filter"""
        days = "7"
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_DAYS_OLD:
                return days
            return default
        
        def mock_get_state_bool(key):
            return key == FF_KEY_DAYS_OLD
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'getStateBool', mock_get_state_bool)
        
        monkeypatch.setattr(vah, 'QRY_SELECT_JOBS_VIEWER', "{selectFields} WHERE {where} ORDER BY {order}", raising=False)
        query = str(vah.getJobListQuery())

        assert 'DATE' in query
        assert 'INTERVAL' in query
        assert '7' in query

    def test_get_job_list_query_with_salary_filter(self, monkeypatch):
        """Test query with salary regex filter"""
        salary_regex = "[0-9]{5,}"
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_SALARY:
                return salary_regex
            return default
        
        def mock_get_state_bool(key):
            return key == FF_KEY_SALARY
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'getStateBool', mock_get_state_bool)
        
        monkeypatch.setattr(vah, 'QRY_SELECT_JOBS_VIEWER', "{selectFields} WHERE {where} ORDER BY {order}", raising=False)
        query = str(vah.getJobListQuery())

        assert 'salary' in query.lower()
        assert salary_regex in query


class TestRemoveFiltersInNotFilters:
    """Test the removeFiltersInNotFilters function"""

    def test_remove_filters_in_not_filters_with_overlap(self, monkeypatch):
        """Test removing filters that appear in both positive and negative lists"""
        bool_fields = ['applied', 'interested']
        not_fields = ['applied', 'seen', 'discarded']
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_BOOL_FIELDS:
                return bool_fields
            elif key == FF_KEY_BOOL_NOT_FIELDS:
                return not_fields
            return default
        
        def mock_get_state_bool_value(key1, key2):
            return True
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'getStateBoolValue', mock_get_state_bool_value)
        
        result = vah.removeFiltersInNotFilters()
        
        # 'applied' should be removed since it's in bool_fields
        assert 'applied' not in result
        # 'seen' and 'discarded' should remain
        assert 'seen' in result
        assert 'discarded' in result

    def test_remove_filters_no_overlap(self, monkeypatch):
        """Test when there's no overlap between positive and negative filters"""
        bool_fields = ['applied']
        not_fields = ['seen', 'discarded']
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_BOOL_FIELDS:
                return bool_fields
            elif key == FF_KEY_BOOL_NOT_FIELDS:
                return not_fields
            return default
        
        def mock_get_state_bool_value(key1, key2):
            return True
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'getStateBoolValue', mock_get_state_bool_value)
        
        result = vah.removeFiltersInNotFilters()
        
        assert result == not_fields

    def test_remove_filters_when_condition_false(self, monkeypatch):
        """Test when the boolean condition is false"""
        not_fields = ['seen', 'discarded']
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_BOOL_NOT_FIELDS:
                return not_fields
            return default
        
        def mock_get_state_bool_value(key1, key2):
            return False
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'getStateBoolValue', mock_get_state_bool_value)
        
        result = vah.removeFiltersInNotFilters()
        
        assert result == not_fields


class TestTableFooter:
    """Test the tableFooter function"""

    def test_table_footer_with_results(self, monkeypatch):
        """Test footer display with results"""
        total_results = 100
        filter_res_cnt = 25
        total_selected = 5
        selected_rows = pd.DataFrame({'id': [1, 2, 3, 4, 5]})
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_SINGLE_SELECT:
                return 1
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        mock_st_write = MagicMock()
        monkeypatch.setattr(vah.st, 'write', mock_st_write)
        mock_st_button = MagicMock(return_value=False)
        monkeypatch.setattr(vah.st, 'button', mock_st_button)
        mock_st_toggle = MagicMock(return_value=True)
        monkeypatch.setattr(vah.st, 'toggle', mock_st_toggle)
        mock_st_number_input = MagicMock(return_value=400)
        monkeypatch.setattr(vah.st, 'number_input', mock_st_number_input)
        monkeypatch.setattr(vah, 'inColumns', MagicMock())
        
        vah.tableFooter(total_results, filter_res_cnt, total_selected, selected_rows)
        
        # Verify st.write was called with footer info
        mock_st_write.assert_called()
        call_args = str(mock_st_write.call_args_list)
        # Should contain the footer with counts
        assert '5' in call_args or '25' in call_args

    def test_table_footer_no_results(self, monkeypatch):
        """Test footer when there are no results"""
        total_results = 100
        filter_res_cnt = 0  # No filtered results
        total_selected = 0
        selected_rows = pd.DataFrame({'id': []})
        
        def mock_get_state(key, default=None):
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        mock_st_write = MagicMock()
        monkeypatch.setattr(vah.st, 'write', mock_st_write)
        
        vah.tableFooter(total_results, filter_res_cnt, total_selected, selected_rows)
        
        # Should still write footer info
        mock_st_write.assert_called()


class TestTableFunction:
    """Test the table function"""

    def test_table_with_single_selection(self, monkeypatch):
        """Test table display with single row selected"""
        df = pd.DataFrame({'id': [1, 2, 3], 'title': ['Job A', 'Job B', 'Job C']})
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_PRESELECTED_ROWS:
                return [0]
            elif key == FF_KEY_LIST_HEIGHT:
                return LIST_HEIGHT
            return default
        
        # Mock st.data_editor to return edited dataframe with selection
        mock_edited_df = df.copy()
        mock_edited_df.insert(0, 'Sel', [True, False, False])
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah.st, 'data_editor', lambda *args, **kwargs: mock_edited_df)
        
        setState_calls = []
        monkeypatch.setattr(vah, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        # Mock preSelectRows behavior
        monkeypatch.setattr(vah, 'preSelectRows', MagicMock())
        monkeypatch.setattr(vah, 'getTableColsConfig', lambda *args, **kwargs: {})
        
        result = vah.table(df, ['id', 'title'], {'title'})
        
        # Verify setState was called with selectedRows
        assert any(k == 'selectedRows' for k, v in setState_calls)

    def test_table_no_selection(self, monkeypatch):
        """Test table when no rows are selected"""
        df = pd.DataFrame({'id': [1, 2], 'title': ['Job A', 'Job B']})
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_LIST_HEIGHT:
                return LIST_HEIGHT
            return default
        
        mock_edited_df = df.copy()
        mock_edited_df.insert(0, 'Sel', [False, False])
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah.st, 'data_editor', lambda *args, **kwargs: mock_edited_df)
        monkeypatch.setattr(vah, 'preSelectRows', MagicMock())
        monkeypatch.setattr(vah, 'getTableColsConfig', lambda *args, **kwargs: {})
        
        setState_calls = []
        monkeypatch.setattr(vah, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        result = vah.table(df, ['id', 'title'], {'title'})
        
        # Should still be called
        assert result is not None


class TestPreSelectRows:
    """Test the preSelectRows function"""

    def test_pre_select_rows_valid_index(self, monkeypatch):
        """Test pre-selecting a valid row"""
        df = pd.DataFrame({'a': [1, 2, 3]})
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_PRESELECTED_ROWS:
                return ['1']
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        
        vah.preSelectRows(df, FF_KEY_PRESELECTED_ROWS)
        
        assert 'Sel' in df.columns
        assert df['Sel'].iloc[1] == True
        assert df['Sel'].iloc[0] == False

    def test_pre_select_rows_out_of_bounds(self, monkeypatch):
        """Test pre-selecting an out of bounds row"""
        df = pd.DataFrame({'a': [1, 2]})
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_PRESELECTED_ROWS:
                return ['10']  # Out of bounds
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        
        vah.preSelectRows(df, FF_KEY_PRESELECTED_ROWS)
        
        assert 'Sel' in df.columns
        # Should not crash, all should be False
        assert df['Sel'].sum() == 0

    def test_pre_select_rows_empty(self, monkeypatch):
        """Test pre-selecting with no pre-selected rows"""
        df = pd.DataFrame({'a': [1, 2, 3]})
        
        def mock_get_state(key, default=None):
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        
        vah.preSelectRows(df, FF_KEY_PRESELECTED_ROWS)
        
        assert 'Sel' in df.columns
        assert df['Sel'].sum() == 0


class TestSelectNext:
    """Test the selectNext function"""

    def test_select_next_valid_transition(self, monkeypatch):
        """Test selecting next row when valid"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_PRESELECTED_ROWS:
                return ['0']
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'setQueryParamOrState',
                          lambda p, pv, sv=None: setState_calls.append((p, sv)))
        
        vah.selectNext(max=5)
        
        # Should have called setQueryParamOrState
        assert len(setState_calls) > 0
        assert setState_calls[0][1] == ['1']

    def test_select_next_at_boundary(self, monkeypatch):
        """Test selecting next at max boundary"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_PRESELECTED_ROWS:
                return ['4']
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'setQueryParamOrState',
                          lambda p, pv, sv=None: setState_calls.append((p, sv)))
        
        vah.selectNext(max=5)

        # Should advance to next row (production code advances when int(rows[0]) < max)
        assert len(setState_calls) > 0
        assert setState_calls[0][1] == ['5']


class TestSelectPrevious:
    """Test the selectPrevious function"""

    def test_select_previous_valid_transition(self, monkeypatch):
        """Test selecting previous row when valid"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_PRESELECTED_ROWS:
                return ['1']
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'setQueryParamOrState',
                          lambda p, pv, sv=None: setState_calls.append((p, sv)))
        
        vah.selectPrevious()
        
        # Should have called setQueryParamOrState
        assert len(setState_calls) > 0
        assert setState_calls[0][1] == ['0']

    def test_select_previous_at_zero(self, monkeypatch):
        """Test selecting previous at row 0"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == FF_KEY_PRESELECTED_ROWS:
                return ['0']
            return default
        
        monkeypatch.setattr(vah, 'getState', mock_get_state)
        monkeypatch.setattr(vah, 'setQueryParamOrState',
                          lambda p, pv, sv=None: setState_calls.append((p, sv)))
        
        vah.selectPrevious()
        
        # Should not go below 0
        assert len(setState_calls) == 0


class TestGetTableColsConfig:
    """Test the getTableColsConfig function"""

    def test_get_table_cols_config_with_selector(self, monkeypatch):
        """Test table column config generation with selector"""
        fields = ['id', 'title', 'company']
        visible = {'title', 'company'}
        
        # Mock st.column_config.Column
        monkeypatch.setattr(vah.st, 'column_config',
                          MagicMock(Column=lambda **kw: f"COL({kw.get('label')})"))
        monkeypatch.setattr(vah, 'CheckboxColumn', lambda **kw: 'CHECKBOX')
        
        # Mock getColumnTranslated
        monkeypatch.setattr(vah, 'getColumnTranslated', lambda c: c.title())
        
        cfg = vah.getTableColsConfig(fields, visible, selector=True)
        
        # Should have Sel and id columns
        assert 'Sel' in cfg
        assert '0' in cfg

    def test_get_table_cols_config_without_selector(self, monkeypatch):
        """Test table column config without selector"""
        fields = ['id', 'title', 'company']
        visible = {'title', 'company'}
        
        monkeypatch.setattr(vah.st, 'column_config',
                          MagicMock(Column=lambda **kw: f"COL({kw.get('label')})"))
        monkeypatch.setattr(vah, 'getColumnTranslated', lambda c: c.title())
        
        cfg = vah.getTableColsConfig(fields, visible, selector=False)
        
        # Should not have Sel column
        assert 'Sel' not in cfg
        assert '0' in cfg
