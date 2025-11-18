from unittest.mock import patch, MagicMock
from viewer.main import PAGES_MAP, main


def test_pages_map_consistency():
    """Test that PAGES_MAP and PAGES are consistent"""
    from viewer.viewConstants import PAGES
    
    # Define expected PAGES_MAP structure
    PAGES_MAP = {0: 'view', 1: 'clean', 2: 'stats'}
    
    assert len(PAGES_MAP) == len(PAGES)
    for key in PAGES_MAP.keys():
        assert key in PAGES

def test_view_constants():
    """Test that view constants are properly defined"""
    from viewer.viewConstants import PAGES, PAGE_STATE_KEY
    
    assert PAGE_STATE_KEY == 'selectedPage'
    assert len(PAGES) == 3
    assert 0 in PAGES
    assert 1 in PAGES  
    assert 2 in PAGES

class TestMain:
    @patch('viewer.main.PAGES_MAP')
    @patch('viewer.main.st')
    @patch('viewer.main.getMessageInfo')
    def test_main_with_selected_view(self, mock_get_message_info, mock_st, mock_pages_map):
        mock_view = MagicMock()
        mock_pages_map.__getitem__.return_value = mock_view
        mock_c1 = MagicMock()
        mock_c2 = MagicMock()
        mock_st.columns.return_value = [mock_c1, mock_c2]
        mock_c1.segmented_control.return_value = 0
        mock_get_message_info.return_value = None
        
        main()
        
        mock_st.set_page_config.assert_called_once_with(layout='wide', page_title="ai job search")
        mock_view.assert_called_once()

    @patch('viewer.main.st')
    @patch('viewer.main.view')
    @patch('viewer.main.getMessageInfo')
    def test_main_with_message_info(self, mock_get_message_info, mock_view, mock_st):
        mock_c1 = MagicMock()
        mock_c2 = MagicMock()
        mock_st.columns.return_value = [mock_c1, mock_c2]
        mock_c1.segmented_control.return_value = None
        mock_get_message_info.return_value = "Test message"
        
        main()
        
        mock_c2.info.assert_called_once_with("Test message")

    @patch('viewer.main.st')
    @patch('viewer.main.view')
    @patch('viewer.main.getMessageInfo')
    def test_main_no_selected_view_defaults_to_view(self, mock_get_message_info, mock_view, mock_st):
        mock_c1 = MagicMock()
        mock_c2 = MagicMock()
        mock_st.columns.return_value = [mock_c1, mock_c2]
        mock_c1.segmented_control.return_value = None
        mock_get_message_info.return_value = None
        
        main()
        
        mock_view.assert_called_once()

    def test_pages_map_structure(self):
        assert 0 in PAGES_MAP
        assert 1 in PAGES_MAP
        assert 2 in PAGES_MAP
        assert len(PAGES_MAP) == 3

    @patch('viewer.main.st')
    @patch('viewer.main.printSessionState')
    @patch('viewer.main.view')
    @patch('viewer.main.getMessageInfo')
    @patch('viewer.main.DEBUG', True)
    def test_main_debug_mode(self, mock_get_message_info, mock_view, 
                           mock_print_session_state, mock_st):
        mock_c1 = MagicMock()
        mock_c2 = MagicMock()
        mock_st.columns.return_value = [mock_c1, mock_c2]
        mock_c1.segmented_control.return_value = None
        mock_get_message_info.return_value = None
        
        main()
        
        mock_print_session_state.assert_called_once()

    @patch('viewer.main.PAGES_MAP')
    @patch('viewer.main.st')
    @patch('viewer.main.getMessageInfo')
    def test_main_clean_page_selected(self, mock_get_message_info, mock_st, mock_pages_map):
        mock_clean = MagicMock()
        mock_pages_map.__getitem__.return_value = mock_clean
        mock_c1 = MagicMock()
        mock_c2 = MagicMock()
        mock_st.columns.return_value = [mock_c1, mock_c2]
        mock_c1.segmented_control.return_value = 1
        mock_get_message_info.return_value = None
        
        main()
        
        mock_clean.assert_called_once()

    @patch('viewer.main.PAGES_MAP')
    @patch('viewer.main.st')
    @patch('viewer.main.getMessageInfo')
    def test_main_stats_page_selected(self, mock_get_message_info, mock_st, mock_pages_map):
        mock_stats = MagicMock()
        mock_pages_map.__getitem__.return_value = mock_stats
        mock_c1 = MagicMock()
        mock_c2 = MagicMock()
        mock_st.columns.return_value = [mock_c1, mock_c2]
        mock_c1.segmented_control.return_value = 2
        mock_get_message_info.return_value = None
        
        main()
        
        mock_stats.assert_called_once()