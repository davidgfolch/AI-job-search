"""
Test package initialization
This file runs before any test modules are imported
"""
import sys
from unittest.mock import MagicMock

# Emergency mocking if conftest hasn't run yet
# This ensures streamlit is mocked even if conftest.py hasn't loaded
if 'streamlit' not in sys.modules or not hasattr(sys.modules.get('streamlit'), '__name__'):
    mock_st = MagicMock()
    mock_st.__name__ = 'streamlit'
    sys.modules['streamlit'] = mock_st
    
    # Mock submodules (but not testing modules)
    for submodule in [
        'streamlit.delta_generator',
        'streamlit.column_config',
        'streamlit.components',
        'streamlit.components.v1',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.proto',
        'streamlit.proto.ButtonGroup_pb2',
    ]:
        sys.modules[submodule] = MagicMock()
    
    # Setup column_config attribute
    mock_st.column_config = MagicMock()
    mock_st.column_config.CheckboxColumn = MagicMock()
    
    # Setup testing attribute - but don't mock AppTest itself
    # Let the real AppTest work for testing
    pass
    
    # Setup proto attribute
    mock_st.proto = MagicMock()
    mock_st.proto.ButtonGroup_pb2 = MagicMock()
    mock_st.proto.ButtonGroup_pb2.ButtonGroup = MagicMock()
    
    # Configure st.columns to return the expected number of columns
    def mock_columns(spec, **kwargs):
        # Accept keyword args (vertical_alignment etc.) used in some calls
        if isinstance(spec, list):
            return [MagicMock() for _ in spec]
        return [MagicMock() for _ in range(spec)]
    
    mock_st.columns = mock_columns