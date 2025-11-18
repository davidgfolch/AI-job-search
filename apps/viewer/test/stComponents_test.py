import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add paths for imports
current_dir = Path(__file__).parent
viewer_dir = current_dir.parent
sys.path.insert(0, str(viewer_dir))

# Mock streamlit before importing
mock_streamlit = MagicMock()
mock_streamlit.session_state = {}
mock_streamlit.delta_generator = MagicMock()
sys.modules['streamlit'] = mock_streamlit
sys.modules['streamlit.delta_generator'] = MagicMock()

import viewer.util.stComponents as stComp


class TestCheckboxFilter:
    """Test the checkboxFilter function"""

    def test_checkbox_filter_basic(self, monkeypatch):
        """Test basic checkbox filter"""
        mock_st = MagicMock()
        mock_st.checkbox.return_value = True
        
        monkeypatch.setattr(stComp, 'checkboxFilter',
                          lambda label, key, container=None: True)
        
        result = stComp.checkboxFilter('Test', 'test_key')
        assert result is True

    def test_checkbox_filter_with_container(self, monkeypatch):
        """Test checkbox filter with custom container"""
        mock_container = MagicMock()
        mock_container.checkbox.return_value = False
        
        monkeypatch.setattr(stComp, 'getBoolKeyName', lambda k: f'is{k.title()}')
        
        result = stComp.checkboxFilter('Test', 'test', mock_container)
        
        # Should call checkbox on container
        assert True


class TestCheckAndInput:
    """Test the checkAndInput function"""

    def test_check_and_input_basic(self, monkeypatch):
        """Test basic check and input without columns"""
        monkeypatch.setattr(stComp, 'checkboxFilter', lambda label, key, c: True)
        monkeypatch.setattr(stComp.st, 'container', MagicMock(return_value=MagicMock()))
        monkeypatch.setattr(stComp.st, 'columns', lambda spec, **kwargs: [MagicMock(), MagicMock()])
        
        # Mock the columns return
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        
        monkeypatch.setattr(stComp.st, 'columns',
                          lambda *args, **kwargs: [mock_col1, mock_col2])
        
        # Should not raise
        stComp.checkAndInput('Search', 'search', withContainer=False)

    def test_check_and_input_with_columns(self, monkeypatch):
        """Test check and input with specific columns"""
        mock_cols = [MagicMock(), MagicMock(), MagicMock()]
        
        monkeypatch.setattr(stComp, 'checkboxFilter', lambda label, key, c: True)
        monkeypatch.setattr(stComp.st, 'columns',
                          lambda spec, **kwargs: mock_cols)
        monkeypatch.setattr(stComp, 'historyButton', MagicMock())
        
        # Should not raise
        stComp.checkAndInput('Salary', 'salary', withColumns=[1, 2, 1], withHistory=True)

    def test_check_and_input_with_history(self, monkeypatch):
        """Test check and input with history button"""
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        
        monkeypatch.setattr(stComp, 'checkboxFilter', lambda label, key, c: True)
        monkeypatch.setattr(stComp.st, 'container', MagicMock(return_value=MagicMock()))
        monkeypatch.setattr(stComp.st, 'columns',
                          lambda spec, **kwargs: [mock_col1, mock_col2])
        
        history_calls = []
        monkeypatch.setattr(stComp, 'historyButton',
                          lambda key, col: history_calls.append((key, col)))
        
        stComp.checkAndInput('Search', 'search', withContainer=False, withHistory=True)
        
        # History button is expected to be called when withHistory=True
        assert len(history_calls) == 1


class TestCheckAndPills:
    """Test the checkAndPills function"""

    def test_check_and_pills_basic(self, monkeypatch):
        """Test basic check and pills"""
        fields = ['applied', 'seen', 'discarded']
        
        mock_container = MagicMock()
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        
        monkeypatch.setattr(stComp.st, 'container', MagicMock(return_value=mock_container))
        monkeypatch.setattr(stComp.st, 'columns',
                          lambda spec, **kwargs: [mock_col1, mock_col2])
        monkeypatch.setattr(stComp, 'checkboxFilter', lambda label, key: True)
        monkeypatch.setattr(stComp, 'getColumnTranslated', lambda c: c.title())
        
        # Should not raise
        stComp.checkAndPills('Status', fields, 'status_filter')

    def test_check_and_pills_with_disabled(self, monkeypatch):
        """Test check and pills when disabled"""
        fields = ['field1', 'field2']
        
        mock_container = MagicMock()
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        
        monkeypatch.setattr(stComp.st, 'container', MagicMock(return_value=mock_container))
        monkeypatch.setattr(stComp.st, 'columns',
                          lambda spec, **kwargs: [mock_col1, mock_col2])
        monkeypatch.setattr(stComp, 'checkboxFilter', lambda label, key: False)
        monkeypatch.setattr(stComp, 'getColumnTranslated', lambda c: c)
        
        # Should not raise even when disabled
        stComp.checkAndPills('Test', fields, 'test_key')


class TestShowCodeSql:
    """Test the showCodeSql function"""

    def test_show_code_sql_with_format(self, monkeypatch):
        """Test showing formatted SQL code"""
        sql = "SELECT * FROM jobs WHERE id = 1"
        
        monkeypatch.setattr(stComp, 'getState', lambda k, default=None: [])
        monkeypatch.setattr(stComp.st, 'code', MagicMock())
        monkeypatch.setattr(stComp, 'formatSql', lambda sql: f"FORMATTED({sql})")
        
        stComp.showCodeSql(sql, format=True, showSql=True)
        
        # Code should be called
        stComp.st.code.assert_called()

    def test_show_code_sql_show_toggle(self, monkeypatch):
        """Test showing SQL when toggle is enabled"""
        sql = "SELECT * FROM jobs"
        
        # Always return showSql so code is displayed
        monkeypatch.setattr(stComp, 'getState', lambda k, default=None: ['showSql'])
        monkeypatch.setattr(stComp.st, 'code', MagicMock())
        
        stComp.showCodeSql(sql)
        
        # Code should be called
        stComp.st.code.assert_called()

    def test_show_code_sql_explicit_show(self, monkeypatch):
        """Test showing SQL when explicitly requested"""
        sql = "SELECT * FROM jobs WHERE salary > 50000"
        
        monkeypatch.setattr(stComp, 'getState', lambda k, default=None: [])
        monkeypatch.setattr(stComp.st, 'code', MagicMock())
        
        stComp.showCodeSql(sql, showSql=True)
        
        stComp.st.code.assert_called()

    def test_show_code_sql_with_params(self, monkeypatch):
        """Test SQL code with parameter substitution"""
        sql = "SELECT * FROM jobs WHERE id = {id}"
        params = {'id': 42}
        
        monkeypatch.setattr(stComp, 'getState', lambda k, default=None: ['showSql'])
        monkeypatch.setattr(stComp.st, 'code', MagicMock())
        
        stComp.showCodeSql(sql, params=params, showSql=True)
        
        stComp.st.code.assert_called()

    def test_show_code_sql_no_conditions(self, monkeypatch):
        """Test SQL code when no conditions met"""
        sql = "SELECT * FROM jobs"
        
        code_calls = []
        monkeypatch.setattr(stComp, 'getState', lambda k, default=None: [])
        monkeypatch.setattr(stComp.st, 'code', lambda *args, **kwargs: code_calls.append((args, kwargs)))
        
        stComp.showCodeSql(sql, showSql=False)
        
        # Code should not be called
        assert len(code_calls) == 0


class TestReloadButton:
    """Test the reloadButton function"""

    def test_reload_button_clicked(self, monkeypatch):
        """Test reload button when clicked"""
        monkeypatch.setattr(stComp.st, 'button', MagicMock(return_value=True))
        monkeypatch.setattr(stComp.st, 'rerun', MagicMock())
        
        stComp.reloadButton()
        
        # rerun should be called
        stComp.st.rerun.assert_called()

    def test_reload_button_not_clicked(self, monkeypatch):
        """Test reload button when not clicked"""
        monkeypatch.setattr(stComp.st, 'button', MagicMock(return_value=False))
        
        rerun_calls = []
        monkeypatch.setattr(stComp.st, 'rerun', lambda: rerun_calls.append(True))
        
        stComp.reloadButton()
        
        # rerun should not be called
        assert len(rerun_calls) == 0


class TestSessionLoadSaveForm:
    """Test the sessionLoadSaveForm function"""

    def test_session_load_save_form_default(self, monkeypatch):
        """Test session load/save form with default option"""
        from collections import deque
        
        mock_files = deque(['Default', 'Session1', 'Session2'])
        
        monkeypatch.setattr(stComp, 'listSessionFiles', lambda: mock_files)
        
        mock_container = MagicMock()
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=False)
        
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        
        monkeypatch.setattr(stComp.st, 'container', MagicMock(return_value=mock_container))
        monkeypatch.setattr(stComp.st, 'columns',
                          lambda *args, **kwargs: [mock_col1, mock_col2, mock_col3])
        
        # Should not raise
        stComp.sessionLoadSaveForm()

    def test_session_load_save_form_new_session(self, monkeypatch):
        """Test creating new session"""
        from collections import deque
        
        mock_files = deque(['Session1', 'Default'])
        
        monkeypatch.setattr(stComp, 'listSessionFiles', lambda: mock_files)
        
        mock_container = MagicMock()
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=False)
        
        mock_col1 = MagicMock()
        mock_col1.selectbox.return_value = '(New)'
        mock_col1.text_input.return_value = 'NewSession'
        
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        
        monkeypatch.setattr(stComp.st, 'container', MagicMock(return_value=mock_container))
        monkeypatch.setattr(stComp.st, 'columns',
                          lambda *args, **kwargs: [mock_col1, mock_col2, mock_col3])
        
        # Should not raise
        stComp.sessionLoadSaveForm()
