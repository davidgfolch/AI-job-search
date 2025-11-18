import pytest
from unittest.mock import MagicMock, Mock, patch
import sys
from pathlib import Path

# Add the parent directory (apps/viewer) to the path so we can import viewer module
# When running: poetry run pytest from apps/viewer/
current_dir = Path(__file__).parent  # apps/viewer/test/
viewer_dir = current_dir.parent       # apps/viewer/
apps_dir = viewer_dir.parent          # apps/
project_root = apps_dir.parent        # project_root/

# Add viewer_dir so we can do: from viewer.viewAndEdit import ...
if str(viewer_dir) not in sys.path:
    sys.path.insert(0, str(viewer_dir))

# Add project root for commonlib
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# This must be done before any imports of the modules being tested
def setup_mocks():
    """Setup all required mocks before imports"""
    
    # Mock streamlit and its submodules
    mock_streamlit = MagicMock()
    
    # Configure st.columns to return the expected number of columns
    def mock_columns(spec, **kwargs):
        # Accept kwargs such as vertical_alignment used by callers
        if isinstance(spec, list):
            return [MagicMock() for _ in spec]
        return [MagicMock() for _ in range(spec)]
    
    mock_streamlit.columns = mock_columns
    mock_streamlit.segmented_control = MagicMock(return_value=0)  # Return valid key
    
    sys.modules['streamlit'] = mock_streamlit
    sys.modules['streamlit.delta_generator'] = MagicMock()
    sys.modules['streamlit.components'] = MagicMock()
    sys.modules['streamlit.components.v1'] = MagicMock()
    sys.modules['streamlit_js_eval'] = MagicMock()
    
    # Mock commonlib modules (if needed)
    if 'commonlib' not in sys.modules:
        sys.modules['commonlib'] = MagicMock()
    if 'commonlib.sqlUtil' not in sys.modules:
        sys.modules['commonlib.sqlUtil'] = MagicMock()
    if 'commonlib.util' not in sys.modules:
        sys.modules['commonlib.util'] = MagicMock()
    if 'commonlib.mysqlUtil' not in sys.modules:
        sys.modules['commonlib.mysqlUtil'] = MagicMock()

# Call setup_mocks immediately
setup_mocks()


@pytest.fixture
def mock_pandas():
    """Fixture to provide a mocked pandas instance"""
    mock_pd = MagicMock()
    mock_df = MagicMock()
    mock_pd.read_sql.return_value = mock_df
    return mock_pd, mock_df


@pytest.fixture
def mock_mysql():
    """Fixture to provide a mocked MySQL connection and utility"""
    with patch('viewer.mysqlConn.mysqlCachedConnection') as mock_cached_conn, \
         patch('commonlib.mysqlUtil.MysqlUtil') as MockMysqlUtil:
        
        # Setup return values
        mock_cached_conn.return_value = Mock()
        
        # Create a mock MysqlUtil instance with common methods
        mock_util = MagicMock()
        mock_util.fetchOne.return_value = (
            1, 'Test Job', 'Test Company', 'Test Client', 
            50000, 'Description', True, False, True,
            None, None, None, None, None
        )
        mock_util.fetchAll.return_value = [
            (1, 'Test Job', 'Test Company', 50000),
            (2, 'Another Job', 'Another Company', 60000)
        ]
        mock_util.count.return_value = 10
        
        MockMysqlUtil.return_value = mock_util
        
        yield mock_util


@pytest.fixture
def mock_streamlit():
    """Fixture to provide a mocked streamlit instance with common components"""
    mock_st = MagicMock()
    
    # Mock session state
    mock_st.session_state = {}
    
    # Mock common streamlit components
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.form.return_value.__enter__ = Mock()
    mock_st.form.return_value.__exit__ = Mock(return_value=False)
    mock_st.expander.return_value.__enter__ = Mock()
    mock_st.expander.return_value.__exit__ = Mock(return_value=False)
    mock_st.container.return_value.__enter__ = Mock()
    mock_st.container.return_value.__exit__ = Mock(return_value=False)
    
    return mock_st


@pytest.fixture
def sample_job_data():
    """Fixture to provide sample job data for testing"""
    from datetime import datetime
    return {
        'id': 1,
        'title': 'Senior Python Developer',
        'company': 'Test Company',
        'client': 'Test Client',
        'salary': '50000-60000',
        'description': 'Test description',
        'applied': True,
        'discarded': False,
        'interested': True,
        'created_at': datetime(2025, 1, 1, 12, 0, 0),
        'modified_at': None,
        'markdown': '# Test Markdown',
        'comments': 'Test comments',
        'required_technologies': 'Python, Django',
        'optional_technologies': 'React, Docker',
        'cv_match_percentage': 85,
        'ai_enrich_error': None
    }


@pytest.fixture
def sample_dataframe():
    """Fixture to provide a sample DataFrame"""
    from pandas import DataFrame
    return DataFrame({
        'id': [1, 2, 3],
        'title': ['Job 1', 'Job 2', 'Job 3'],
        'company': ['Company A', 'Company B', 'Company C'],
        'salary': ['50k', '60k', '70k']
    })


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test"""
    yield
    # Clean up after test if needed


@pytest.fixture
def mock_constants():
    """Fixture to provide mocked constants from viewAndEditConstants"""
    constants = MagicMock()
    constants.DB_FIELDS = 'id, title, company, client, salary'
    constants.DEFAULT_BOOL_FILTERS = ['applied', 'interested']
    constants.DEFAULT_NOT_FILTERS = ['discarded']
    constants.DEFAULT_ORDER = 'created_at DESC'
    constants.DEFAULT_SQL_FILTER = ''
    constants.DEFAULT_DAYS_OLD = 30
    constants.FIELDS_BOOL = ['applied', 'discarded', 'interested']
    constants.LIST_VISIBLE_COLUMNS = ['title', 'company', 'salary']
    constants.LIST_HEIGHT = 400
    return constants