from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from streamlit.proto.ButtonGroup_pb2 import ButtonGroup
from streamlit.delta_generator import DeltaGenerator

from viewer.main import PAGES_MAP, PAGES
from viewer.viewConstants import PAGE_STATE_KEY
from viewer.viewAndEdit import view
from viewer.util.stStateUtil import setState


def test_pages_map_consistency():
    """Test that PAGES_MAP and PAGES are consistent"""
    assert len(PAGES_MAP) == len(PAGES)
    for key in PAGES_MAP.keys():
        assert key in PAGES


@patch('viewer.dashboard.stats')
@patch('viewer.cleaner.clean')
@patch('viewer.viewAndEdit.view')
def test_page_navigation(mock_view, mock_clean, mock_stats):
    app_test = AppTest.from_file("viewer/main.py")
    app = app_test.run()
    print(f'app.columns={app.columns}')
    assert len(app.columns) == 2
    c1: DeltaGenerator = app.columns[0]
    assert len(c1.children) == 1
    buttonGroup: ButtonGroup = c1.children[0]
    assert buttonGroup.key == PAGE_STATE_KEY
    assert len(buttonGroup.options) == len(PAGES)
    for k in PAGES.keys():
        assert buttonGroup.options[k].content == PAGES[k]
    mock_view.assert_called_once()
    mock_view.reset_mock()

    app_test = AppTest.from_file("viewer/main.py")
    app_test.session_state[PAGE_STATE_KEY] = 0
    app = app_test.run()
    mock_view.assert_called_once()

    app_test = AppTest.from_file("viewer/main.py")
    app_test.session_state[PAGE_STATE_KEY] = 1
    app = app_test.run()
    mock_clean.assert_called_once()

    app_test = AppTest.from_file("viewer/main.py")
    app_test.session_state[PAGE_STATE_KEY] = 2
    app = app_test.run()
    mock_stats.assert_called_once()

