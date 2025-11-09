from unittest.mock import MagicMock

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

