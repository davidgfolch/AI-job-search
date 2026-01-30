import pytest
from unittest.mock import patch, MagicMock
from ..dataExtractor import dataExtractor, _save, DataExtractor, _getJobIdsList

@pytest.fixture
def mock_deps():
    with patch('aiEnrich.dataExtractor.MysqlUtil') as mysql_util, \
         patch('aiEnrich.dataExtractor._save') as save_chk, \
         patch('aiEnrich.dataExtractor.printJob'), patch('aiEnrich.dataExtractor.printHR'), \
         patch('aiEnrich.dataExtractor.footer'), patch('aiEnrich.dataExtractor.StopWatch'), \
         patch('aiEnrich.dataExtractor.combineTaskResults'), patch('aiEnrich.dataExtractor.mapJob'), \
         patch('aiEnrich.dataExtractor.AiEnrichRepository') as repo_cls:
        
        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql
        
        repo = MagicMock()
        repo_cls.return_value = repo
        
        yield {'mysql': mysql, 'save': save_chk, 'repo': repo}

class TestDataExtractor:
    
    @patch('aiEnrich.dataExtractor._getJobIdsList', return_value=[1])
    @patch('aiEnrich.dataExtractor.DataExtractor')
    def test_extractor_success(self, mock_cls, mock_ids, mock_deps):
        """Test success"""
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')
        
        crew_mock = MagicMock()
        mock_cls.return_value.crew.return_value = crew_mock
        
        with patch('aiEnrich.dataExtractor.combineTaskResults', return_value={'salary': '100k'}), \
             patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            assert dataExtractor() == 1
            mock_deps['save'].assert_called()

    def test_save(self, mock_deps):
        """Test save"""
        repo = MagicMock()
        with patch('aiEnrich.dataExtractor.validateResult'):
            _save(repo, 1, {'salary': '100k', 'required_technologies': 'T', 'optional_technologies': 'O'})
            repo.update_enrichment.assert_called_once_with(1, '100k', 'T', 'O')