import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import pandas as pd
from ..cvMatcher import cvMatch, save, loadCVContent, extractTextFromPDF, getJobIdsList, CVMatcher

@pytest.fixture
def mock_deps():
    with patch('aiEnrich.cvMatcher.getEnvBool') as env, \
         patch('aiEnrich.cvMatcher.loadCVContent') as load_cv, \
         patch('aiEnrich.cvMatcher.MysqlUtil') as mysql_util, \
         patch('aiEnrich.cvMatcher.save') as save_chk, \
         patch('aiEnrich.cvMatcher.printJob'), patch('aiEnrich.cvMatcher.printHR'), \
         patch('aiEnrich.cvMatcher.footer'), patch('aiEnrich.cvMatcher.StopWatch'), \
         patch('aiEnrich.cvMatcher.cvContent', 'CV content'):
        env.return_value = True
        load_cv.return_value = True
        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql
        yield {'env': env, 'load_cv': load_cv, 'mysql': mysql, 'save': save_chk}

class TestCVMatcher:
    @pytest.mark.parametrize("env_bool, loaded, count, expected", [(False, 1, 1, 0), (True, 0, 1, 0), (True, 1, 0, 0)])
    def test_cv_match_early_exits(self, mock_deps, env_bool, loaded, count, expected):
        """Test early exits"""
        mock_deps['env'].return_value = env_bool
        mock_deps['load_cv'].return_value = bool(loaded)
        mock_deps['mysql'].count.return_value = count
        assert cvMatch() == expected

    @patch('aiEnrich.cvMatcher.getJobIdsList', return_value=[1])
    @patch('aiEnrich.cvMatcher.CVMatcher')
    def test_cv_match_success(self, mock_cls, mock_ids, mock_deps):
        """Test success"""
        mock_deps['mysql'].count.return_value = 1
        mock_deps['mysql'].fetchOne.return_value = (1, 'Job', 'Desc', 'Comp')
        mock_cls.return_value.crew.return_value.kickoff.return_value.raw = '{"cv_match_percentage": 85}'
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

    @patch('pdfplumber.open')
    def test_extract_text_from_pdf(self, mock_pdf):
        """Test PDF extract"""
        page = MagicMock()
        page.extract_text.return_value = "Text"
        page.extract_tables.return_value = [[['H1'], ['R1']]]
        mock_pdf.return_value.__enter__.return_value.pages = [page]
        with patch.object(pd.DataFrame, 'to_markdown', return_value='| H1 |'):
            res = extractTextFromPDF('a.pdf')
            assert 'Text' in res and '| H1 |' in res

    @pytest.mark.parametrize("env_v, suf, p_exists, t_exists", [('a.pd', '.pd', 1, 0), ('a.pdf', '.pdf', 0, 0), ('a.pdf', '.pdf', 0, 0)])
    def test_load_cv_content_failures(self, mock_deps, env_v, suf, p_exists, t_exists):
        """Test load failures"""
        mock_deps['env'].side_effect = [True, env_v] # First call for check, second for val? No, fixture handles bool.
        # Actually loadCVContent calls getEnvBool then getEnv. fixture mocks getEnvBool. 
        # But getEnv also needs mocking. 
        # And we need to ensure cvContent is None
        
        # NOTE: logic in loadCVContent:
        # 1. getEnvBool -> False? return False. (Covered in test_cv_match_early_exits implicitly? No, that tests cvMatch calling it. This tests loadCVContent directly.)
        # Here we test failures after check passed.
        
        with patch('aiEnrich.cvMatcher.getEnv', return_value=env_v), \
             patch('aiEnrich.cvMatcher.Path') as mock_path, \
             patch('aiEnrich.cvMatcher.cvContent', None), \
             patch('aiEnrich.cvMatcher.CV_LOCATION', env_v): # Use env_v as loc
            
            p, t = MagicMock(), MagicMock()
            p.exists.return_value, p.suffix.lower.return_value = bool(p_exists), suf
            t.exists.return_value = bool(t_exists)
            mock_path.side_effect = [p, t]
            assert loadCVContent() is False

    @patch('aiEnrich.cvMatcher.CV_LOCATION', 'a.pdf')
    @patch('aiEnrich.cvMatcher.getEnv', return_value='a.pdf')
    @patch('aiEnrich.cvMatcher.Path')
    @patch('builtins.open', new_callable=mock_open, read_data='CV')
    def test_load_cv_content_txt_fallback(self, mock_f, mock_p, mock_e, mock_deps):
        """Test txt fallback"""
        p, t = MagicMock(), MagicMock()
        p.exists.return_value, p.suffix.lower.return_value = False, '.pdf'
        t.exists.return_value = True
        mock_p.side_effect = [p, t]
        with patch('aiEnrich.cvMatcher.cvContent', None):
            assert loadCVContent() is True
            mock_f.assert_called()

    @patch('aiEnrich.cvMatcher.CV_LOCATION', 'a.pdf')
    @patch('aiEnrich.cvMatcher.getEnv', return_value='a.pdf')
    @patch('aiEnrich.cvMatcher.Path')
    @patch('aiEnrich.cvMatcher.extractTextFromPDF', return_value='PDF')
    def test_load_cv_content_pdf_success(self, mock_ex, mock_p, mock_e, mock_deps):
        """Test PDF success"""
        p, t = MagicMock(), MagicMock()
        p.exists.return_value, p.suffix.lower.return_value = True, '.pdf'
        t.exists.return_value = False
        mock_p.side_effect = [p, t]
        with patch('aiEnrich.cvMatcher.cvContent', None), patch('builtins.open', mock_open()):
            assert loadCVContent() is True
            mock_ex.assert_called_with('a.pdf')

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