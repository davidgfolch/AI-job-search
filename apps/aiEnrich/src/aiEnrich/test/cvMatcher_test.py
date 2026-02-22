import pytest
from unittest.mock import patch, MagicMock
from ..cvMatcher import cvMatch, _save, CVMatcher

@pytest.fixture
def mock_deps():
    with patch('aiEnrich.cvMatcher.getEnvBool') as env, \
         patch('aiEnrich.cvMatcher.MysqlUtil') as mysql_util, \
         patch('aiEnrich.cvMatcher._save') as save_chk, \
         patch('aiEnrich.cvMatcher.printJob'), patch('aiEnrich.cvMatcher.printHR'), \
         patch('aiEnrich.cvMatcher.footer'), patch('aiEnrich.cvMatcher.StopWatch'), \
         patch('aiEnrich.cvMatcher.combineTaskResults'), patch('aiEnrich.cvMatcher.mapJob'), \
         patch('aiEnrich.cvMatcher.AiEnrichRepository') as repo_cls:
        
        env.return_value = True

        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql
        
        repo = MagicMock()
        repo_cls.return_value = repo
        
        yield {'env': env, 'mysql': mysql, 'save': save_chk, 'repo': repo}

class TestCVMatcher:
    def test_cv_match_early_exits_loader_false(self, mock_deps):
        """Test early exit if cvContent is empty"""
        assert cvMatch("") == 0

    @patch('aiEnrich.cvMatcher.CVMatcher')
    def test_cv_match_success(self, mock_cls, mock_deps):
        """Test success"""
        mock_deps['repo'].count_pending_cv_match.return_value = 1
        mock_deps['repo'].get_pending_cv_match_ids.return_value = [1]
        mock_deps['repo'].get_job_to_match_cv.return_value = (1, 'Job', 'Desc', 'Comp')
        
        crew_mock = MagicMock()
        mock_cls.return_value.crew.return_value = crew_mock
        
        with patch('aiEnrich.cvMatcher.combineTaskResults', return_value={'cv_match_percentage': 85}), \
             patch('aiEnrich.cvMatcher.mapJob', return_value=('Job', 'Comp', 'Desc')):
            assert cvMatch("Mock CV") == 1
            mock_deps['save'].assert_called()

    def test_save(self, mock_deps):
        """Test save"""
        repo = MagicMock()
        with patch('aiEnrich.cvMatcher.validateResult'):
            _save(repo, 1, {'cv_match_percentage': 85})
            repo.update_cv_match.assert_called_once_with(1, 85)

    def test_classes(self):
        """Test classes"""
        m = CVMatcher()
        assert isinstance(m.agents_config, dict)
        with patch('aiEnrich.cvMatcher.Agent'), patch('aiEnrich.cvMatcher.getEnv', return_value='300'), \
             patch('aiEnrich.cvMatcher.Task'), patch('aiEnrich.cvMatcher.Crew'):
            m.agents_config = {'cv_matcher_agent': {'role': 'R'}}
            m.cv_matcher_agent()
            m.tasks_config = {'cv_matcher_task': {'description': 'D'}}
            m.cv_matcher_task()
            with patch.object(m, 'cv_matcher_agent'), patch.object(m, 'cv_matcher_task'):
                m.crew()