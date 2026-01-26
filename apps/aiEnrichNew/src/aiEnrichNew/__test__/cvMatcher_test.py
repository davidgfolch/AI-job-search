import pytest
from unittest.mock import patch, MagicMock
from ..cvMatcher import FastCVMatcher

@pytest.fixture
def mock_cv_matcher_deps():
    with patch('aiEnrichNew.cvMatcher.SentenceTransformer') as st, \
         patch('aiEnrichNew.cvMatcher.CVLoader') as loader_cls, \
         patch('aiEnrichNew.cvMatcher.getEnvBool', return_value=True):
        
        st_instance = MagicMock()
        st.return_value = st_instance
        st_instance.encode.return_value = [[0.1, 0.2]]
        
        loader = MagicMock()
        loader_cls.return_value = loader
        loader.load_cv_content.return_value = True
        loader.get_content.return_value = "Mock CV"
        
        yield {'st': st_instance, 'loader': loader}

def test_fast_cv_matcher_initialization(mock_cv_matcher_deps):
    FastCVMatcher._instance = None # Reset singleton
    matcher = FastCVMatcher.instance()
    assert matcher._model is not None
    assert matcher._cv_loader is not None

def test_fast_cv_matcher_process_db(mock_cv_matcher_deps):
    FastCVMatcher._instance = None
    matcher = FastCVMatcher.instance()
    
    with patch('aiEnrichNew.cvMatcher.MysqlUtil') as mysql_util:
        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql
        mysql.count.return_value = 1
        mysql.fetchAll.return_value = [(1,)]
        mysql.fetchOne.return_value = (1, 'Title', b'Desc', 'Comp')
        
        matcher.process_db_jobs()
        
        mysql.updateFromAI.assert_called()

def test_match(mock_cv_matcher_deps):
    FastCVMatcher._instance = None
    matcher = FastCVMatcher.instance()
    # Need to trigger load
    matcher._load_cv_content()
    
    res = matcher.match("Job Desc")
    assert 'cv_match_percentage' in res
