import pytest
from unittest.mock import patch, MagicMock
from ..cvMatcher import cvMatch, save, CVMatcher, getJobIdsList

@pytest.fixture
def mock_deps():
    with patch('aiEnrich.cvMatcher.getEnvBool') as env, \
         patch('aiEnrich.cvMatcher.CVLoader') as cv_loader_cls, \
         patch('aiEnrich.cvMatcher.MysqlUtil') as mysql_util, \
         patch('aiEnrich.cvMatcher.save') as save_chk, \
         patch('aiEnrich.cvMatcher.printJob'), patch('aiEnrich.cvMatcher.printHR'), \
         patch('aiEnrich.cvMatcher.footer'), patch('aiEnrich.cvMatcher.StopWatch'), \
         patch('aiEnrich.cvMatcher.combineTaskResults'), patch('aiEnrich.cvMatcher.mapJob'):
        
        env.return_value = True
        
        cv_loader_instance = MagicMock()
        cv_loader_cls.return_value = cv_loader_instance
        cv_loader_instance.load_cv_content.return_value = True
        cv_loader_instance.get_content.return_value = "Mock CV"
        
        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql
        
        yield {'env': env, 'cv_loader': cv_loader_instance, 'mysql': mysql, 'save': save_chk}

class TestCVMatcher:
    def test_cv_match_early_exits_loader_false(self, mock_deps):
        """Test early exit if loader returns False"""
        mock_deps['cv_loader'].load_cv_content.return_value = False
        assert cvMatch() == 0

    @patch('aiEnrich.cvMatcher.getJobIdsList', return_value=[1])
    @patch('aiEnrich.cvMatcher.CVMatcher')
    def test_cv_match_success(self, mock_cls, mock_ids, mock_deps):
        """Test success"""
        mock_deps['mysql'].count.return_value = 1
        mock_deps['mysql'].fetchOne.return_value = (1, 'Job', 'Desc', 'Comp')
        
        crew_mock = MagicMock()
        mock_cls.return_value.crew.return_value = crew_mock
        
        # combineTaskResults is mocked in fixture
        with patch('aiEnrich.cvMatcher.combineTaskResults', return_value={'cv_match_percentage': 85}), \
             patch('aiEnrich.cvMatcher.mapJob', return_value=('Job', 'Comp', 'Desc')):
            assert cvMatch() == 1
            mock_deps['save'].assert_called()

    def test_save(self, mock_deps):
        """Test save"""
        with patch('aiEnrich.cvMatcher.validateResult'), \
             patch('aiEnrich.cvMatcher.maxLen', return_value=(85, 1)), \
             patch('aiEnrich.cvMatcher.emptyToNone', return_value=(85, 1)):
            save(mock_deps['mysql'], 1, {'cv_match_percentage': 85})
            mock_deps['mysql'].updateFromAI.assert_called_once()

    def test_get_job_ids_list(self):
        """Test get job IDs"""
        mysql = MagicMock()
        mysql.fetchAll.return_value = [(1,), (2,), (3,)]
        with patch('aiEnrich.cvMatcher.yellow'):
            assert getJobIdsList(mysql) == [1, 2, 3]

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