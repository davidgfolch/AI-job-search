import traceback
from unittest.mock import patch, MagicMock
from commonlib.exceptionUtil import getProjectTraceItems

def test_getProjectTraceItems_basic():
    try:
        raise ValueError("Test error")
    except ValueError as e:
        trace = getProjectTraceItems(e)
        # Should contain current filename
        assert "exceptionUtil_test.py" in trace

@patch('traceback.extract_tb')
def test_getProjectTraceItems_filtering(mock_extract_tb):
    # Setup mock frames
    frame_site_packages = MagicMock()
    frame_site_packages.filename = '/usr/lib/python3.8/site-packages/somelib/module.py'
    frame_site_packages.lineno = 10
    
    frame_user_code = MagicMock()
    frame_user_code.filename = '/projects/app/main.py'
    frame_user_code.lineno = 20

    mock_extract_tb.return_value = [frame_site_packages, frame_user_code]
    
    # Create a dummy exception logic since we are mocking extract_tb which takes the traceback
    class DummyException:
        __traceback__ = "dummy_traceback"

    result = getProjectTraceItems(DummyException())
    
    # Assert 'site-packages' file is filtered out
    assert 'module.py' not in result
    # Assert user code is present
    assert 'main.py:20' in result
