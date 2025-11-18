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

import viewer.viewAndEditEvents as vae


class TestOnTableChange:
    """Test the onTableChange callback function"""

    def test_on_table_change_single_select_no_last_selected(self, monkeypatch):
        """Test onTableChange when FF_KEY_SINGLE_SELECT is true but no lastSelected exists"""
        monkeypatch.setattr(vae, 'getState', lambda key, default=None: {
            vae.FF_KEY_SINGLE_SELECT: 1,
            'lastSelected': None,
            'jobsListTable': {'edited_rows': [0]}
        }.get(key, default))
        
        setState_calls = []
        monkeypatch.setattr(vae, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        vae.onTableChange()
        
        # Should set preselected rows to [0]
        assert any(k == vae.FF_KEY_PRESELECTED_ROWS for k, v in setState_calls)
        assert any(k == 'lastSelected' for k, v in setState_calls)

    def test_on_table_change_single_select_with_last_selected(self, monkeypatch):
        """Test onTableChange when single select is enabled with previous selection"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == vae.FF_KEY_SINGLE_SELECT:
                return 1
            elif key == 'lastSelected':
                return {'edited_rows': [0]}
            elif key == 'jobsListTable':
                return {'edited_rows': [1]}
            return default

        monkeypatch.setattr(vae, 'getState', mock_get_state)
        monkeypatch.setattr(vae, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        vae.onTableChange()
        
        # Should have called setState for FF_KEY_PRESELECTED_ROWS with new selection
        preselected_calls = [v for k, v in setState_calls if k == vae.FF_KEY_PRESELECTED_ROWS]
        assert len(preselected_calls) > 0

    def test_on_table_change_multiple_select(self, monkeypatch):
        """Test onTableChange when single select is disabled (multiple select)"""
        setState_calls = []
        
        def mock_get_state(key, default=None):
            if key == vae.FF_KEY_SINGLE_SELECT:
                return 0  # Multiple select mode
            return default

        monkeypatch.setattr(vae, 'getState', mock_get_state)
        monkeypatch.setattr(vae, 'setState', lambda k, v: setState_calls.append((k, v)))
        
        vae.onTableChange()
        
        # Should still update lastSelected
        assert any(k == 'lastSelected' for k, v in setState_calls)


class TestMarkAs:
    """Test the markAs function"""

    def test_mark_as_with_selected_rows(self, monkeypatch):
        """Test marking selected rows with a boolean field"""
        mock_ids = ['1', '2', '3']
        mock_query = 'UPDATE jobs SET field=TRUE WHERE id IN (1,2,3)'
        mock_params = {}
        
        monkeypatch.setattr(vae, 'getSelectedRowsIds', lambda x: mock_ids)
        monkeypatch.setattr(vae, 'updateFieldsQuery', 
                          lambda ids, fields: (mock_query, mock_params))
        monkeypatch.setattr(vae, 'showCodeSql', MagicMock())
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 3

        # Patch the module-level MysqlUtil factory to return our mock
        monkeypatch.setattr(vae, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        message_info_calls = []
        monkeypatch.setattr(vae, 'setMessageInfo', 
                          lambda msg: message_info_calls.append(msg))
        
        vae.markAs('applied')
        
        # Verify database operation was called
        mock_mysql_util.executeAndCommit.assert_called_once_with(mock_query, mock_params)
        
        # Verify message was set
        assert len(message_info_calls) > 0
        assert 'APPLIED' in message_info_calls[0]

    def test_mark_as_no_selected_rows(self, monkeypatch):
        """Test markAs when no rows are selected"""
        monkeypatch.setattr(vae, 'getSelectedRowsIds', lambda x: [])
        
        message_info_calls = []
        monkeypatch.setattr(vae, 'setMessageInfo', 
                          lambda msg: message_info_calls.append(msg))
        
        vae.markAs('seen')
        
        # Should not set any message since no rows selected
        assert len(message_info_calls) == 0

    def test_mark_as_single_row(self, monkeypatch):
        """Test marking a single row"""
        mock_ids = ['42']
        mock_query = 'UPDATE jobs SET interested=TRUE WHERE id=42'
        mock_params = {}
        
        monkeypatch.setattr(vae, 'getSelectedRowsIds', lambda x: mock_ids)
        monkeypatch.setattr(vae, 'updateFieldsQuery',
                          lambda ids, fields: (mock_query, mock_params))
        monkeypatch.setattr(vae, 'showCodeSql', MagicMock())
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 1
        
        monkeypatch.setattr(vae, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        message_info_calls = []
        monkeypatch.setattr(vae, 'setMessageInfo',
                          lambda msg: message_info_calls.append(msg))
        
        vae.markAs('interested')
        
        assert len(message_info_calls) > 0
        assert '1 row' in message_info_calls[0]


class TestDeleteSelectedRows:
    """Test the deleteSelectedRows function"""

    def test_delete_selected_rows_with_ids(self, monkeypatch):
        """Test deleting selected rows"""
        mock_ids = ['1', '2', '3']
        mock_query = 'DELETE FROM jobs WHERE id IN (1,2,3)'
        
        monkeypatch.setattr(vae, 'getSelectedRowsIds', lambda x: mock_ids)
        monkeypatch.setattr(vae, 'deleteJobsQuery', lambda ids: mock_query)
        monkeypatch.setattr(vae, 'showCodeSql', MagicMock())
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 3
        
        monkeypatch.setattr(vae, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        st_info_calls = []
        monkeypatch.setattr(vae.st, 'info',
                          lambda msg: st_info_calls.append(msg))
        
        vae.deleteSelectedRows()
        
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
        monkeypatch.setattr(vae, 'getSelectedRowsIds', lambda x: [])
        
        st_info_calls = []
        monkeypatch.setattr(vae.st, 'info',
                          lambda msg: st_info_calls.append(msg))
        
        vae.deleteSelectedRows()
        
        # Should not display info message
        assert len(st_info_calls) == 0

    def test_delete_selected_rows_single_row(self, monkeypatch):
        """Test deleting a single row"""
        mock_ids = ['99']
        mock_query = 'DELETE FROM jobs WHERE id=99'
        
        monkeypatch.setattr(vae, 'getSelectedRowsIds', lambda x: mock_ids)
        monkeypatch.setattr(vae, 'deleteJobsQuery', lambda ids: mock_query)
        monkeypatch.setattr(vae, 'showCodeSql', MagicMock())
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 1
        
        monkeypatch.setattr(vae, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        st_info_calls = []
        monkeypatch.setattr(vae.st, 'info',
                          lambda msg: st_info_calls.append(msg))
        
        vae.deleteSelectedRows()
        
        assert len(st_info_calls) > 0
        assert '1 job' in st_info_calls[0]


class TestDeleteSalary:
    """Test the deleteSalary function"""

    def test_delete_salary(self, monkeypatch):
        """Test deleting salary for a specific job"""
        job_id = 42
        
        mock_mysql_util = MagicMock()
        mock_mysql_util.executeAndCommit.return_value = 1
        
        monkeypatch.setattr(vae, 'MysqlUtil', lambda *args, **kwargs: mock_mysql_util)
        
        vae.deleteSalary(job_id)
        
        # Verify the correct query was executed
        call_args = mock_mysql_util.executeAndCommit.call_args
        assert 'update jobs set salary=null' in call_args[0][0].lower()
        assert f'id = {job_id}' in call_args[0][0]


class TestKeysToColumns:
    """Test the keysToColumns function"""

    def test_keys_to_columns_single_form_field(self):
        """Test converting form field keys to column names"""
        input_dict = {'formStatus': 'active', 'formComments': 'test'}
        result = vae.keysToColumns(input_dict)
        
        assert 'Status' in result
        assert 'Comments' in result
        assert result['Status'] == 'active'
        assert result['Comments'] == 'test'

    def test_keys_to_columns_preserves_non_form_keys(self):
        """Test that non-form keys are preserved as-is"""
        input_dict = {'formStatus': 'active', 'other_key': 'value'}
        result = vae.keysToColumns(input_dict)
        
        assert result['other_key'] == 'value'
        assert 'Status' in result

    def test_keys_to_columns_empty_dict(self):
        """Test with empty input dictionary"""
        result = vae.keysToColumns({})
        assert result == {}

    def test_keys_to_columns_complex_form_fields(self):
        """Test with multiple form fields"""
        input_dict = {
            'formSalary': 50000,
            'formCompany': 'Tech Corp',
            'formClient': 'Client A',
            'formComments': 'Good fit'
        }
        result = vae.keysToColumns(input_dict)
        
        assert 'Salary' in result
        assert 'Company' in result
        assert 'Client' in result
        assert 'Comments' in result
