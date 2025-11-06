from unittest.mock import MagicMock, Mock, patch
from streamlit.testing.v1 import AppTest
from streamlit.proto.ButtonGroup_pb2 import ButtonGroup
from streamlit.delta_generator import DeltaGenerator

# def test_pages_map_consistency():
#     """Test that PAGES_MAP and PAGES are consistent"""
#     assert len(PAGES_MAP) == len(PAGES)
#     for key in PAGES_MAP.keys():
#         assert key in PAGES


@patch('viewer.dashboard.stats')
@patch('viewer.cleaner.clean')
@patch('viewer.viewAndEdit.view')
def test_page_navigation(mock_view: MagicMock, mock_clean, mock_stats):

    with patch('viewer.viewAndEdit.mysqlCachedConnection') as mock_cachedConn, \
         patch('commonlib.mysqlUtil.getConnection') as mock_conn, \
            patch('commonlib.mysqlUtil.MysqlUtil') as MockMysqlUtil:
        mock_conn.return_value = MagicMock()    
        mock_conn.return_value = Mock()
        MockMysqlUtil.return_value = Mock()

        from viewer.main import PAGES_MAP, PAGES
        from viewer.viewConstants import PAGE_STATE_KEY

        appTest = AppTest.from_file("viewer/main.py")
        app = appTest.run()
        print(f'app.columns={app.columns}')
        assert len(app.columns) == 2
        c1: DeltaGenerator = app.columns[0]
        assert len(c1.children) == 1
        buttonGroup: ButtonGroup = c1.children[0]
        assert buttonGroup.key == PAGE_STATE_KEY
        assert len(buttonGroup.options) == len(PAGES)
        for k in PAGES.keys():
            assert buttonGroup.options[k].content == PAGES[k]
        mock_view.assert_called()
        mock_view.reset_mock()

        appTest = AppTest.from_file("viewer/main.py")
        appTest.session_state[PAGE_STATE_KEY] = 0
        app = appTest.run()
        mock_view.assert_called_once()

        appTest = AppTest.from_file("viewer/main.py")
        appTest.session_state[PAGE_STATE_KEY] = 1
        app = appTest.run()
        mock_clean.assert_called_once()

        appTest = AppTest.from_file("viewer/main.py")
        appTest.session_state[PAGE_STATE_KEY] = 2
        app = appTest.run()
        mock_stats.assert_called_once()

