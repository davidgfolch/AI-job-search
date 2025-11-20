import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add paths for imports
current_dir = Path(__file__).parent
viewer_dir = current_dir.parent
sys.path.insert(0, str(viewer_dir))

# Mock streamlit before importing viewer modules
mock_streamlit = MagicMock()
mock_streamlit.session_state = {}
sys.modules['streamlit'] = mock_streamlit

import viewer.viewAndEditEvents as sut


class TestOnTableChange:
    """Test the onTableChange callback function"""

    def test_on_table_change_single_select_no_last_selected(self, monkeypatch):
        """Test onTableChange when FF_KEY_SINGLE_SELECT is true but no lastSelected exists"""
        monkeypatch.setattr(sut, 'getState', lambda key, default=None: {
            sut.FF_KEY_SINGLE_SELECT: 1,
            'lastSelected': None,
            'jobsListTable': {'edited_rows': [0]}
        }.get(key, default))
        
        setState_calls = []
        monkeypatch.setattr(sut, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        sut.onTableChange()
        
        # Should set preselected rows to [0]
        assert any(k == sut.FF_KEY_PRESELECTED_ROWS for k, v in setState_calls)
        assert any(k == 'lastSelected' for k, v in setState_calls)

    def test_on_table_change_single_select_with_last_selected(self, monkeypatch):
        """Test onTableChange when single select is enabled with previous selection"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == sut.FF_KEY_SINGLE_SELECT:
                return 1
            elif key == 'lastSelected':
                return {'edited_rows': [0]}
            elif key == 'jobsListTable':
                return {'edited_rows': [1]}
            return default

        monkeypatch.setattr(sut, 'getState', mock_get_state)
        monkeypatch.setattr(sut, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        sut.onTableChange()
        
        # Should have called setState for FF_KEY_PRESELECTED_ROWS with new selection
        preselected_calls = [v for k, v in setState_calls if k == sut.FF_KEY_PRESELECTED_ROWS]
        assert len(preselected_calls) > 0

    def test_on_table_change_multiple_select(self, monkeypatch):
        """Test onTableChange when single select is disabled (multiple select)"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == sut.FF_KEY_SINGLE_SELECT:
                return 0  # Multiple select mode
            return default

        monkeypatch.setattr(sut, 'getState', mock_get_state)
        monkeypatch.setattr(sut, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        sut.onTableChange()
        
        # Should still update lastSelected
        assert any(k == 'lastSelected' for k, v in setState_calls)


class TestMarkAs:
    """Test the markAs function"""

    def test_mark_as_with_selected_rows(self, monkeypatch):
        """Test marking selected rows with a boolean field"""
        mock_ids = ['1', '2', '3']
        mock_query = 'UPDATE jobs SET field=TRUE WHERE id IN (1,2,3)'
        mock_params = {}
        
        monkeypatch.setattr(sut, 'getSelectedRowsIds', lambda x: mock_ids)
        monkeypatch.setattr(sut, 'updateFieldsQuery', 
                          lambda ids, fields: (mock_query, mock_params))
        monkeypatch.setattr(sut, 'showCodeSql', MagicMock())
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 3

        # Patch the module-level MysqlUtil factory to return our mock
        monkeypatch.setattr(sut, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        message_info_calls = []
        monkeypatch.setattr(sut, 'setMessageInfo', 
                          lambda msg: message_info_calls.append(msg))
        
        sut.markAs('applied')
        
        # Verify database operation was called
        mock_mysql_util.executeAndCommit.assert_called_once_with(mock_query, mock_params)
        
        # Verify message was set
        assert len(message_info_calls) > 0
        assert 'APPLIED' in message_info_calls[0]

    def test_mark_as_no_selected_rows(self, monkeypatch):
        """Test markAs when no rows are selected"""
        monkeypatch.setattr(sut, 'getSelectedRowsIds', lambda x: [])
        
        message_info_calls = []
        monkeypatch.setattr(sut, 'setMessageInfo', 
                          lambda msg: message_info_calls.append(msg))
        
        sut.markAs('seen')
        
        # Should not set any message since no rows selected
        assert len(message_info_calls) == 0

    def test_mark_as_single_row(self, monkeypatch):
        """Test marking a single row"""
        mock_ids = ['42']
        mock_query = 'UPDATE jobs SET interested=TRUE WHERE id=42'
        mock_params = {}
        
        monkeypatch.setattr(sut, 'getSelectedRowsIds', lambda x: mock_ids)
        monkeypatch.setattr(sut, 'updateFieldsQuery',
                          lambda ids, fields: (mock_query, mock_params))
        monkeypatch.setattr(sut, 'showCodeSql', MagicMock())
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 1
        
        monkeypatch.setattr(sut, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        message_info_calls = []
        monkeypatch.setattr(sut, 'setMessageInfo',
                          lambda msg: message_info_calls.append(msg))
        
        sut.markAs('interested')
        
        assert len(message_info_calls) > 0
        assert '1 row' in message_info_calls[0]


class TestDeleteSelectedRows:
    """Test the deleteSelectedRows function"""

    def test_delete_selected_rows_with_ids(self, monkeypatch):
        """Test deleting selected rows"""
        mock_ids = ['1', '2', '3']
        mock_query = 'DELETE FROM jobs WHERE id IN (1,2,3)'
        
        monkeypatch.setattr(sut, 'getSelectedRowsIds', lambda x: mock_ids)
        monkeypatch.setattr(sut, 'deleteJobsQuery', lambda ids: mock_query)
        monkeypatch.setattr(sut, 'showCodeSql', MagicMock())
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 3
        
        monkeypatch.setattr(sut, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        st_info_calls = []
        monkeypatch.setattr(sut.st, 'info', lambda msg: st_info_calls.append(msg))
        
        sut.deleteSelectedRows()
        
        # Verify database operation
        mock_mysql_util.executeAndCommit.assert_called_once_with(mock_query)
        
        # Verify success message
        assert len(st_info_calls) > 0
        assert '3 job' in st_info_calls[0]
        # Message includes Ids list (strings) — ensure the ids are present
        assert 'Ids:' in st_info_calls[0]
        assert "'1'" in st_info_calls[0] and "'2'" in st_info_calls[0] and "'3'" in st_info_calls[0]

    def test_delete_selected_rows_no_ids(self, monkeypatch):
        """Test deleteSelectedRows when no rows are selected"""
        monkeypatch.setattr(sut, 'getSelectedRowsIds', lambda x: [])
        
        st_info_calls = []
        monkeypatch.setattr(sut.st, 'info', lambda msg: st_info_calls.append(msg))
        
        sut.deleteSelectedRows()
        
        # Should not display info message
        assert len(st_info_calls) == 0

    def test_delete_selected_rows_single_row(self, monkeypatch):
        """Test deleting a single row"""
        mock_ids = ['99']
        mock_query = 'DELETE FROM jobs WHERE id=99'
        
        monkeypatch.setattr(sut, 'getSelectedRowsIds', lambda x: mock_ids)
        monkeypatch.setattr(sut, 'deleteJobsQuery', lambda ids: mock_query)
        monkeypatch.setattr(sut, 'showCodeSql', MagicMock())
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 1
        
        monkeypatch.setattr(sut, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        st_info_calls = []
        monkeypatch.setattr(sut.st, 'info', lambda msg: st_info_calls.append(msg))
        
        sut.deleteSelectedRows()
        
        assert len(st_info_calls) > 0
        assert '1 job' in st_info_calls[0]


class TestDeleteSalary:
    """Test the deleteSalary function"""

    def test_delete_salary(self, monkeypatch):
        """Test deleting salary for a specific job"""
        job_id = 42
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 1
        
        monkeypatch.setattr(sut, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        sut.deleteSalary(job_id)
        
        # Verify the correct query was executed
        call_args = mock_mysql_util.executeAndCommit.call_args
        assert 'update jobs set salary=null' in call_args[0][0].lower()
        assert f'id = {job_id}' in call_args[0][0]


class TestKeysToColumns:
    """Test the keysToColumns function"""

    def test_keys_to_columns_single_form_field(self):
        """Test converting form field keys to column names"""
        input_dict = {'formStatus': 'active', 'formComments': 'test'}
        result = sut.keysToColumns(input_dict)
        
        assert 'Status' in result
        assert 'Comments' in result
        assert result['Status'] == 'active'
        assert result['Comments'] == 'test'

    def test_keys_to_columns_preserves_non_form_keys(self):
        """Test that non-form keys are preserved as-is"""
        input_dict = {'formStatus': 'active', 'other_key': 'value'}
        result = sut.keysToColumns(input_dict)
        
        assert result['other_key'] == 'value'
        assert 'Status' in result

    def test_keys_to_columns_empty_dict(self):
        """Test with empty input dictionary"""
        result = sut.keysToColumns({})
        assert result == {}

    def test_keys_to_columns_complex_form_fields(self):
        """Test with multiple form fields"""
        input_dict = {
            'formSalary': 50000,
            'formCompany': 'Tech Corp',
            'formClient': 'Client A',
            'formComments': 'Good fit'
        }
        result = sut.keysToColumns(input_dict)
        
        assert 'Salary' in result
        assert 'Company' in result
        assert 'Client' in result
        assert 'Comments' in result
