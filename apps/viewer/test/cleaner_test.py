import sys
from pathlib import Path
from unittest.mock import MagicMock
import pandas as pd

# Add paths for imports
current_dir = Path(__file__).parent
viewer_dir = current_dir.parent
sys.path.insert(0, str(viewer_dir))

# Mock streamlit before importing viewer modules
mock_streamlit = MagicMock()
mock_streamlit.session_state = {}
sys.modules['streamlit'] = mock_streamlit

import viewer.cleaner as cleaner
from viewer.viewConstants import PAGE_VIEW_IDX


class TestClean:
    """Test the clean function"""

    def test_clean_with_results(self, monkeypatch):
        """Test clean function with query results"""
        mock_query = "SELECT id, title FROM jobs WHERE created < DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        mock_rows = [
            (1, 'Job Title 1'),
            (2, 'Job Title 2')
        ]
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchAll.return_value = mock_rows
        mock_mysql_util.getTableDdlColumnNames.return_value = ['id', 'title', 'company']
        
        monkeypatch.setattr(cleaner, 'MysqlUtil', lambda x: mock_mysql_util)
        monkeypatch.setattr(cleaner.st, 'columns', lambda spec: [MagicMock() for _ in range(2)])
        
        # Create mock selectbox column
        mock_col = MagicMock()
        mock_col.selectbox.return_value = 0
        
        # Mock the columns context manager
        def mock_columns_context(spec):
            if isinstance(spec, list):
                cols = [MagicMock() for _ in spec]
                cols[0].selectbox.return_value = 0
                cols[1].number_input = MagicMock()
                return cols
            return [MagicMock() for _ in range(spec)]
        
        monkeypatch.setattr(cleaner.st, 'columns', mock_columns_context)
        
        # Mock other streamlit components
        monkeypatch.setattr(cleaner.st, 'warning', MagicMock())
        monkeypatch.setattr(cleaner, 'showQuery', MagicMock(return_value=mock_query))
        monkeypatch.setattr(cleaner, 'table', MagicMock(return_value=(
            pd.DataFrame(mock_rows), pd.DataFrame(mock_rows)
        )))
        monkeypatch.setattr(cleaner, 'tableSummary', MagicMock(return_value=2))
        monkeypatch.setattr(cleaner, 'actionButtons', MagicMock())
        
        # Should not raise
        cleaner.clean()

    def test_clean_no_results(self, monkeypatch):
        """Test clean function when no results found"""
        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchAll.return_value = []
        
        monkeypatch.setattr(cleaner, 'MysqlUtil', lambda x: mock_mysql_util)
        monkeypatch.setattr(cleaner.st, 'columns', lambda spec: [MagicMock() for _ in range(2)])
        
        mock_col = MagicMock()
        mock_col.selectbox.return_value = 0
        
        def mock_columns_context(spec):
            cols = [MagicMock() for _ in spec]
            cols[0].selectbox.return_value = 0
            return cols
        
        monkeypatch.setattr(cleaner.st, 'columns', mock_columns_context)
        monkeypatch.setattr(cleaner.st, 'warning', MagicMock())
        monkeypatch.setattr(cleaner, 'showQuery', MagicMock(return_value='SELECT * FROM jobs'))
        
        cleaner.clean()
        
        # Should show warning
        cleaner.st.warning.assert_called()


class TestResetState:
    """Test the resetState function"""

    def test_reset_state(self, monkeypatch):
        """Test that resetState clears session state"""
        setState_calls = []
        monkeypatch.setattr(cleaner, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        cleaner.resetState()
        
        # Should have called setState with 'lastSelected' and None
        assert any(k == 'lastSelected' for k, v in setState_calls)
        assert any(v is None for k, v in setState_calls)


class TestTable:
    """Test the table function"""

    def test_table_with_selected_rows(self, monkeypatch):
        """Test table display with selected rows"""
        query_cols = ['Ids', 'Title', 'Company']
        res = [
            ('1', 'Python Dev', 'TechCorp'),
            ('2', 'Java Dev', 'DataCorp')
        ]
        columns = ['id', 'title', 'company', 'salary']
        
        config = {
            'dfCols': query_cols,
            'sql': lambda: 'SELECT * FROM jobs',
            'actionButtonFnc': MagicMock()
        }
        
        # Create test dataframe
        df = pd.DataFrame(res, columns=query_cols)
        
        # Mock getState to return selected row
        def mock_get_state(key, default=None):
            if key == 'lastSelected':
                return None
            elif key == 'selectAll':
                return False
            return default
        
        # Create mock edited df
        edited_df = df.copy()
        edited_df.insert(0, 'Sel', [True, False])
        
        monkeypatch.setattr(cleaner, 'getState', mock_get_state)
        monkeypatch.setattr(cleaner.st, 'data_editor',
                          lambda *args, **kwargs: edited_df)
        monkeypatch.setattr(cleaner.st, 'column_config', MagicMock())
        
        setState_calls = []
        monkeypatch.setattr(cleaner, 'setState', lambda k, v: setState_calls.append((k, v)))
        monkeypatch.setattr(cleaner, 'onTableChange', MagicMock())
        
        editedDf, selectedRows = cleaner.table(columns, config, res)
        
        # Verify table was called
        assert editedDf is not None
        assert selectedRows is not None

    def test_table_select_all(self, monkeypatch):
        """Test table with select all enabled"""
        query_cols = ['Ids', 'Title']
        res = [('1', 'Job1'), ('2', 'Job2')]
        columns = ['id', 'title']
        config = {'dfCols': query_cols}
        
        df = pd.DataFrame(res, columns=query_cols)
        
        def mock_get_state(key, default=None):
            if key == 'selectAll':
                return True
            return default
        
        edited_df = df.copy()
        edited_df.insert(0, 'Sel', [True, True])
        
        monkeypatch.setattr(cleaner, 'getState', mock_get_state)
        monkeypatch.setattr(cleaner.st, 'data_editor',
                          lambda *args, **kwargs: edited_df)
        monkeypatch.setattr(cleaner.st, 'column_config', MagicMock())
        
        setState_calls = []
        monkeypatch.setattr(cleaner, 'setState', lambda k, v: setState_calls.append((k, v)))
        monkeypatch.setattr(cleaner, 'onTableChange', MagicMock())
        
        editedDf, selectedRows = cleaner.table(columns, config, res)
        
        # All rows should be selected
        assert editedDf['Sel'].sum() > 0


class TestOnTableChange:
    """Test the onTableChange function in cleaner module"""

    def test_on_table_change_selection_update(self, monkeypatch):
        """Test onTableChange when selection is updated"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == 'cleanJobsListTable':
                # emulate edited_rows as a mapping of row index -> edited values
                return {'edited_rows': {0: {'Sel': True}, 2: {'Sel': True}}}
            elif key == 'lastSelected':
                return {0: {'Sel': True}, 1: {'Sel': False}}
            return default
        
        monkeypatch.setattr(cleaner, 'getState', mock_get_state)
        monkeypatch.setattr(cleaner, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        cleaner.onTableChange()
        
        # Should have called setState with 'lastSelected'
        assert any(k == 'lastSelected' for k, v in setState_calls)

    def test_on_table_change_no_last_selected(self, monkeypatch):
        """Test onTableChange when no previous selection"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == 'cleanJobsListTable':
                return {'edited_rows': [0]}
            elif key == 'lastSelected':
                return None
            return default
        
        monkeypatch.setattr(cleaner, 'getState', mock_get_state)
        monkeypatch.setattr(cleaner, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        cleaner.onTableChange()
        
        # Should still update lastSelected
        assert any(k == 'lastSelected' for k, v in setState_calls)


class TestTableSummary:
    """Test the tableSummary function"""

    def test_table_summary_with_ids(self, monkeypatch):
        """Test tableSummary returns count of selected rows"""
        selected_rows = pd.DataFrame({
            'Ids': ['1,2,3'],
            'Title': ['Job1']
        })
        
        mock_getAllIds = MagicMock(return_value='1,2,3')
        monkeypatch.setattr(cleaner, 'getAllIds', mock_getAllIds)
        
        # tableSummary expects (rows, selectedRows)
        result = cleaner.tableSummary(selected_rows, selected_rows)
        
        # Should return number of selected rows
        assert isinstance(result, int)

    def test_table_summary_no_rows(self, monkeypatch):
        """Test tableSummary with no selected rows"""
        selected_rows = pd.DataFrame({'Ids': []})
        
        mock_getAllIds = MagicMock(return_value='')
        monkeypatch.setattr(cleaner, 'getAllIds', mock_getAllIds)
        
        # tableSummary expects (rows, selectedRows)
        result = cleaner.tableSummary(selected_rows, selected_rows)
        
        assert result == 0


class TestActionButtons:
    """Test the actionButtons function"""

    def test_action_buttons_with_selected_rows(self, monkeypatch):
        """Test action buttons when rows are selected"""
        selected_rows = pd.DataFrame({
            'Ids': ['1', '2'],
            'Title': ['Job1', 'Job2']
        })
        total_selected = 2
        
        config = {
            'actionButtonFnc': MagicMock()
        }
        
        mock_columns = [MagicMock(), MagicMock()]
        monkeypatch.setattr(cleaner.st, 'columns', lambda spec: mock_columns)
        monkeypatch.setattr(cleaner.st, 'dataframe', MagicMock())
        
        # Get the first column mock
        col1 = mock_columns[0]
        col1.button = MagicMock()
        
        monkeypatch.setattr(cleaner, 'getAllIds', MagicMock(return_value='1,2'))
        monkeypatch.setattr(cleaner, 'gotoPage', MagicMock())
        
        cleaner.actionButtons(config, selected_rows, total_selected)
        
        # Verify buttons were created
        assert col1.button.called

    def test_action_buttons_disabled(self, monkeypatch):
        """Test action buttons when disabled (no selection)"""
        selected_rows = pd.DataFrame({'Ids': []})
        total_selected = 0
        
        config = {
            'actionButtonFnc': MagicMock()
        }
        
        mock_columns = [MagicMock(), MagicMock()]
        monkeypatch.setattr(cleaner.st, 'columns', lambda spec: mock_columns)
        monkeypatch.setattr(cleaner.st, 'dataframe', MagicMock())
        
        col1 = mock_columns[0]
        col1.button = MagicMock()
        
        cleaner.actionButtons(config, selected_rows, total_selected)
        
        # Buttons should be disabled when no selection
        call_args_list = col1.button.call_args_list
        # At least one button call should have disabled=True
        assert any('disabled' in str(call) for call in call_args_list)


class TestShowQuery:
    """Test the showQuery function"""

    def test_show_query_displays_sql(self, monkeypatch):
        """Test that showQuery displays the query"""
        query = "SELECT * FROM jobs WHERE created > DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        
        mock_c2 = MagicMock()
        monkeypatch.setattr(cleaner.st, 'columns', lambda spec: [MagicMock(), mock_c2])
        monkeypatch.setattr(mock_c2, 'code', MagicMock())
        monkeypatch.setattr(cleaner.st, 'toggle', lambda *a, **k: False)

        result = cleaner.showQuery(mock_c2, query)
        
        # Should return the query
        assert result == query

    def test_show_query_returns_query(self, monkeypatch):
        """Test that showQuery returns the passed query"""
        query = "SELECT id FROM jobs"
        mock_c2 = MagicMock()
        monkeypatch.setattr(cleaner.st, 'toggle', lambda *a, **k: False)

        result = cleaner.showQuery(mock_c2, query)
        
        assert result == query
