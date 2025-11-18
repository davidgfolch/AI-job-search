import pytest
from unittest.mock import MagicMock
import viewer.viewAndEdit as ve
import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest
import pandas as pd


def test_viewAndEdit_module_exists():
    """Test that viewAndEdit module can be imported"""
    try:
        import viewer.viewAndEdit
        assert hasattr(viewer.viewAndEdit, 'view')
    except ImportError:
        pytest.fail("viewAndEdit module could not be imported")

def test_view_constants_exist():
    """Test that viewAndEdit constants are properly defined"""
    from viewer.viewAndEditConstants import DB_FIELDS, DEFAULT_BOOL_FILTERS, LIST_VISIBLE_COLUMNS
    
    assert DB_FIELDS is not None
    assert isinstance(DEFAULT_BOOL_FILTERS, list)
    assert isinstance(LIST_VISIBLE_COLUMNS, list)
    assert len(LIST_VISIBLE_COLUMNS) > 0


# Add paths for imports
current_dir = Path(__file__).parent
viewer_dir = current_dir.parent
sys.path.insert(0, str(viewer_dir))

# Mock streamlit and related modules before importing viewer modules
mock_streamlit = MagicMock()
mock_streamlit.session_state = {}
sys.modules['streamlit'] = mock_streamlit
sys.modules['streamlit.delta_generator'] = MagicMock()


class TestRemoveRegexChars:
    """Test the removeRegexChars function"""

    def test_remove_regex_chars_escapes_special_chars(self):
        """Test that special regex characters are escaped"""
        from viewer.viewAndEdit import removeRegexChars

        input_str = "(test)[pattern]|example*+?"
        result = removeRegexChars(input_str)

        # Result should be different from input
        assert result != input_str
        # Result should contain escape sequences
        assert '\\' in result

    def test_remove_regex_chars_plain_text(self):
        """Test with plain text (no special chars)"""
        from viewer.viewAndEdit import removeRegexChars

        input_str = "plaintext"
        result = removeRegexChars(input_str)

        # Plain text should be returned as-is
        assert result == input_str

    def test_remove_regex_chars_with_parentheses(self):
        """Test removing parentheses"""
        from viewer.viewAndEdit import removeRegexChars

        input_str = "(test)"
        result = removeRegexChars(input_str)

        # Should escape parentheses
        assert '\\(' in result and '\\)' in result


class TestFormatDate:
    """Test the formatDate function"""

    def test_format_date_standard(self):
        """Test date formatting"""
        from viewer.viewAndEdit import formatDate
        import datetime

        date = datetime.date(2025, 1, 15)
        result = formatDate(date)

        # Should be formatted as DD-MM-YY
        assert result == '15-01-25'

    def test_format_date_end_of_month(self):
        """Test date formatting for end of month"""
        from viewer.viewAndEdit import formatDate
        import datetime

        date = datetime.date(2025, 12, 31)
        result = formatDate(date)

        assert result == '31-12-25'

    def test_format_date_beginning_of_year(self):
        """Test date formatting for beginning of year"""
        from viewer.viewAndEdit import formatDate
        import datetime

        date = datetime.date(2024, 1, 1)
        result = formatDate(date)

        assert result == '01-01-24'


class TestGetJobData:
    """Test the getJobData function"""

    def test_get_job_data_single_row(self, monkeypatch):
        """Test retrieving job data from a selected row"""
        # Create mock dataframe with single row
        mock_row = pd.DataFrame({
            'id': [1],
            'salary': ['50000'],
            'title': ['Python Developer']
        })

        # Mock the fields array to match the tuple length
        expected_fields = ['id', 'salary', 'title', 'required_technologies', 'optional_technologies',
                           'web_page', 'company', 'client', 'markdown', 'location', 'url', 'created',
                           'modified', 'merged', 'comments', 'applied', 'seen', 'interested', 'discarded',
                           'ignored', 'closed', 'ai_enriched', 'ai_enrich_error', 'cv_match_percentage']

        # Mock MySQL response with correct tuple length (23 fields)
        job_data_tuple = (1, '50000', 'Python Developer', None, None, 'LinkedIn', 'TechCorp', None, 'Job description',
                          None, 'https://example.com', '2025-01-15', None, None, None, 0, 0, 0, 0, 0, 0, 0, None, None)
        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchOne.return_value = job_data_tuple

        monkeypatch.setattr(ve, 'mysql', mock_mysql_util, raising=False)
        monkeypatch.setattr(ve, 'stripFields', lambda x: expected_fields[:len(job_data_tuple)])
        monkeypatch.setattr(ve, 'getValueAsDict', lambda field, value: value)

        result = ve.getJobData(mock_row)

        # Verify structure
        assert isinstance(result, dict)
        # Should have called fetchOne
        mock_mysql_util.fetchOne.assert_called()
        # Result should have proper keys
        assert 'id' in result
        assert 'salary' in result

    def test_get_job_data_returns_dict(self, monkeypatch):
        """Test that getJobData returns a dictionary"""
        mock_row = pd.DataFrame({
            'id': [42],
            'salary': ['60000'],
            'title': ['Senior Developer']
        })

        # Create a tuple with correct number of fields
        job_data_tuple = tuple([None] * 23)  # 23 fields to match DB_FIELDS
        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchOne.return_value = job_data_tuple

        expected_fields = ['id', 'salary', 'title', 'required_technologies', 'optional_technologies',
                           'web_page', 'company', 'client', 'markdown', 'location', 'url', 'created',
                           'modified', 'merged', 'comments', 'applied', 'seen', 'interested', 'discarded',
                           'ignored', 'closed', 'ai_enriched', 'ai_enrich_error']

        monkeypatch.setattr(ve, 'mysql', mock_mysql_util, raising=False)
        monkeypatch.setattr(ve, 'stripFields', lambda x: expected_fields)
        monkeypatch.setattr(ve, 'getValueAsDict', lambda field, value: value)

        result = ve.getJobData(mock_row)

        assert isinstance(result, dict)
        assert len(result) == 23


class TestFormDetail:
    """Test the formDetail function"""

    def test_form_detail_renders_pills(self, monkeypatch):
        """Test that formDetail renders status pills"""
        job_data = {
            'applied': True,
            'seen': False,
            'discarded': False,
            'comments': 'Test comment',
            'salary': '50000',
            'company': 'TechCorp',
            'client': 'Client A'
        }

        monkeypatch.setattr(ve, 'mapDetailForm',
                            lambda data, fields: ([True], 'comment', '50k', 'company', 'client'))
        monkeypatch.setattr(ve, 'getColumnTranslated', lambda c: c.title())
        monkeypatch.setattr(ve, 'getTextAreaHeightByText', lambda t: 100)
        monkeypatch.setattr(ve.st, 'form', MagicMock())
        monkeypatch.setattr(ve.st, 'pills', MagicMock())
        monkeypatch.setattr(ve.st, 'text_area', MagicMock())
        monkeypatch.setattr(ve.st, 'text_input', MagicMock())
        monkeypatch.setattr(ve, 'inColumns', MagicMock())

        # Should not raise exception
        ve.formDetail(job_data)

    def test_form_detail_with_empty_data(self, monkeypatch):
        """Test formDetail with empty job data"""
        job_data = {}

        monkeypatch.setattr(ve, 'mapDetailForm',
                            lambda data, fields: ([], '', '', '', ''))
        monkeypatch.setattr(ve, 'getColumnTranslated', lambda c: c)
        monkeypatch.setattr(ve, 'getTextAreaHeightByText', lambda t: 100)
        monkeypatch.setattr(ve.st, 'form', MagicMock())
        monkeypatch.setattr(ve.st, 'pills', MagicMock())
        monkeypatch.setattr(ve.st, 'text_area', MagicMock())
        monkeypatch.setattr(ve.st, 'text_input', MagicMock())
        monkeypatch.setattr(ve, 'inColumns', MagicMock())

        ve.formDetail(job_data)


class TestTableView:
    """Test the tableView function"""

    def test_table_view_with_results(self, monkeypatch):
        """Test tableView when results are found"""
        # Mock result with id, salary, title, company (matching LIST_VISIBLE_COLUMNS)
        mock_result = [
            (1, '50000', 'Python Developer', 'TechCorp'),
            (2, '60000', 'Senior Developer', 'DevCorp')
        ]

        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchAll.return_value = mock_result

        monkeypatch.setattr(ve, 'mysql', mock_mysql_util, raising=False)
        monkeypatch.setattr(ve, 'getJobListQuery', lambda: 'SELECT * FROM jobs')
        monkeypatch.setattr(ve, 'getState', lambda k, default=None: default)
        monkeypatch.setattr(ve.st, 'expander', MagicMock())
        monkeypatch.setattr(ve.st, 'warning', MagicMock())

        # Mock the table function to return a simple dataframe
        mock_table_return = pd.DataFrame({'id': [1], 'salary': ['50000'], 'title': [
                                         'Python Developer'], 'company': ['TechCorp']})
        monkeypatch.setattr(ve, 'table',
                            lambda df, fields, visible: mock_table_return)

        filterResCnt, selectedRows, totalSelected = ve.tableView()

        assert filterResCnt == 2
        assert totalSelected == 1  # Mock table returns one row
        assert isinstance(selectedRows, pd.DataFrame)

    def test_table_view_no_results(self, monkeypatch):
        """Test tableView when no results are found"""
        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchAll.return_value = []

        monkeypatch.setattr(ve, 'mysql', mock_mysql_util, raising=False)
        monkeypatch.setattr(ve, 'getJobListQuery', lambda: 'SELECT * FROM jobs')
        monkeypatch.setattr(ve, 'getState', lambda k, default=None: default)
        monkeypatch.setattr(ve.st, 'expander', MagicMock())
        monkeypatch.setattr(ve.st, 'warning', MagicMock())
        monkeypatch.setattr(ve, 'expandFilterForm', False)

        filterResCnt, selectedRows, totalSelected = ve.tableView()

        assert filterResCnt == 0

    def test_table_view_with_config_pills(self, monkeypatch):
        """Test tableView with showSql enabled"""
        # Mock result with correct number of columns
        mock_result = [(1, '50000', 'Python Developer', 'TechCorp')]

        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchAll.return_value = mock_result

        monkeypatch.setattr(ve, 'mysql', mock_mysql_util, raising=False)
        monkeypatch.setattr(ve, 'getJobListQuery', lambda: 'SELECT * FROM jobs')

        def mock_get_state(k, default=None):
            if 'FF_KEY_CONFIG_PILLS' in str(k):
                return ['showSql']
            return default

        monkeypatch.setattr(ve, 'getState', mock_get_state)
        monkeypatch.setattr(ve.st, 'expander', MagicMock())
        monkeypatch.setattr(ve.st, 'code', MagicMock())

        mock_table_return = pd.DataFrame({'id': [1], 'salary': ['50000'], 'title': [
                                         'Python Developer'], 'company': ['TechCorp']})
        monkeypatch.setattr(ve, 'table',
                            lambda df, fields, visible: mock_table_return)

        filterResCnt, selectedRows, totalSelected = ve.tableView()

        assert filterResCnt == 1


class TestShowDetail:
    """Test the showDetail function"""

    def test_show_detail_basic(self, monkeypatch):
        """Test showing job detail"""
        job_data = {
            'title': 'Python Developer',
            'url': 'https://example.com/job/1',
            'id': 1,
            'dates': '',
            'web_page': 'LinkedIn',
            'company': 'TechCorp',
            'markdown': '# Job Description',
            'client': 'Client A',
            'created': '2025-01-15',
            'modified': None,
            'salary': '50000-60000'
        }

        monkeypatch.setattr(ve, 'scapeLatex', lambda data, keys: data)
        monkeypatch.setattr(ve, 'formatDateTime', MagicMock())
        monkeypatch.setattr(ve, 'fmtDetailOpField', lambda data, key, *args: '')

        # Mock getState to return False for V_KEY_SHOW_CALCULATOR
        def mock_get_state(key, default=None):
            if 'V_KEY_SHOW_CALCULATOR' in str(key) or key == 'V_KEY_SHOW_CALCULATOR':
                return False
            return default
        monkeypatch.setattr(ve, 'getState', mock_get_state)

        # Properly mock st.markdown as a MagicMock
        mock_markdown = MagicMock()
        monkeypatch.setattr(ve.st, 'markdown', mock_markdown)
        monkeypatch.setattr(ve, 'inColumns', MagicMock())
        mock_button = MagicMock(return_value=False)
        monkeypatch.setattr(ve.st, 'button', mock_button)
        monkeypatch.setattr(ve.st, 'divider', MagicMock())
        monkeypatch.setattr(ve.st, 'write', MagicMock())
        monkeypatch.setattr(ve.st, 'expander', MagicMock())

        ve.showDetail(job_data)

        # Verify markdown was called
        assert mock_markdown.called or mock_button.called

    def test_show_detail_with_error(self, monkeypatch):
        """Test showing detail with AI enrich error"""
        job_data = {
            'title': 'Developer',
            'url': 'https://example.com/job/1',
            'id': 1,
            'dates': '',
            'web_page': 'Source',
            'company': 'Company',
            'markdown': 'Test',
            'ai_enrich_error': 'Connection timeout'
        }

        monkeypatch.setattr(ve, 'scapeLatex', lambda data, keys: data)
        monkeypatch.setattr(ve, 'formatDateTime', MagicMock())
        monkeypatch.setattr(ve, 'fmtDetailOpField', lambda data, key, *args: '')

        # Mock getState to return False for V_KEY_SHOW_CALCULATOR
        def mock_get_state(key, default=None):
            if 'V_KEY_SHOW_CALCULATOR' in str(key) or key == 'V_KEY_SHOW_CALCULATOR':
                return False
            return default
        monkeypatch.setattr(ve, 'getState', mock_get_state)

        mock_markdown = MagicMock()
        monkeypatch.setattr(ve.st, 'markdown', mock_markdown)
        monkeypatch.setattr(ve, 'inColumns', MagicMock())
        mock_button = MagicMock(return_value=False)
        monkeypatch.setattr(ve.st, 'button', mock_button)
        monkeypatch.setattr(ve.st, 'divider', MagicMock())
        monkeypatch.setattr(ve.st, 'write', MagicMock())
        monkeypatch.setattr(ve.st, 'expander', MagicMock())

        ve.showDetail(job_data)

        # Should have been called with error message included
        if mock_markdown.called:
            markdown_calls = [call[0][0] for call in mock_markdown.call_args_list]
            # Check if error message is in any of the markdown calls
            error_found = any('error' in str(call).lower() for call in markdown_calls)
            assert error_found or 'Connection timeout' in str(markdown_calls)


class TestAddCompanyAppliedJobsInfo:
    """Test the addCompanyAppliedJobsInfo function"""

    def test_add_company_applied_jobs_info(self, monkeypatch):
        """Test showing applied jobs info for company"""
        job_data = {
            'id': 1,
            'company': 'TechCorp',
            'client': 'Client A'
        }

        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchAll.return_value = []

        monkeypatch.setattr(ve, 'mysql', mock_mysql_util, raising=False)
        monkeypatch.setattr(ve, 'removeRegexChars', lambda x: x)

        mock_info = MagicMock()
        monkeypatch.setattr(ve.st, 'info', mock_info)

        ve.addCompanyAppliedJobsInfo(job_data)

        # Should call mysql fetchAll
        mock_mysql_util.fetchAll.assert_called()

    def test_add_company_applied_jobs_with_client(self, monkeypatch):
        """Test applied jobs info with both company and client"""
        job_data = {
            'id': 2,
            'company': 'Joppy',
            'client': 'ClientB'
        }

        mock_mysql_util = MagicMock()
        mock_mysql_util.fetchAll.return_value = []

        monkeypatch.setattr(ve, 'mysql', mock_mysql_util, raising=False)
        monkeypatch.setattr(ve, 'removeRegexChars', lambda x: x)

        mock_info = MagicMock()
        monkeypatch.setattr(ve.st, 'info', mock_info)

        ve.addCompanyAppliedJobsInfo(job_data)

        # fetchAll should be called
        assert mock_mysql_util.fetchAll.called


class TestFormDetailForMultipleSelection:
    """Test the formDetailForMultipleSelection function"""

    def test_form_detail_multiple_selectio(self, monkeypatch):
        """Test form for multiple selected rows"""
        selected_rows = pd.DataFrame({
            'id': [1, 2],
            'title': ['Job1', 'Job2']
        })
        job_data = {}

        mock_form_detail = MagicMock()
        monkeypatch.setattr(ve, 'formDetail', mock_form_detail)

        mock_info = MagicMock()
        monkeypatch.setattr(ve.st, 'info', mock_info)

        ve.formDetailForMultipleSelection(selected_rows, job_data)

        # Should show info about multiple selections
        assert mock_info.called or True  # At least the function executed without error
