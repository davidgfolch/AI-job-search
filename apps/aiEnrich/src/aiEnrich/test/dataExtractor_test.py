import pytest
from unittest.mock import patch, MagicMock
from ..dataExtractor import dataExtractor, _save, _getJobIdsList

@pytest.fixture
def mock_deps():
    with patch('aiEnrich.dataExtractor.MysqlUtil') as mysql_util, \
         patch('aiEnrich.dataExtractor._save') as save_chk, \
         patch('aiEnrich.dataExtractor.printJob'), patch('aiEnrich.dataExtractor.printHR'), \
         patch('aiEnrich.dataExtractor.footer'), patch('aiEnrich.dataExtractor.StopWatch'), \
         patch('aiEnrich.dataExtractor.rawToJson'), patch('aiEnrich.dataExtractor.mapJob'), \
         patch('aiEnrich.dataExtractor.AiEnrichRepository') as repo_cls, \
         patch('aiEnrich.dataExtractor.query_ollama') as mock_ollama:

        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql

        repo = MagicMock()
        repo_cls.return_value = repo

        yield {'mysql': mysql, 'save': save_chk, 'repo': repo, 'ollama': mock_ollama}

class TestDataExtractor:

    @patch('aiEnrich.dataExtractor._getJobIdsList', return_value=[1])
    def test_extractor_success(self, mock_ids, mock_deps):
        """Test success"""
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')

        with patch('aiEnrich.dataExtractor.rawToJson', return_value={'salary': '100k'}), \
             patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            mock_deps['ollama'].return_value = '{"salary": "100k"}'
            assert dataExtractor() == 1
            mock_deps['save'].assert_called()
            mock_deps['ollama'].assert_called_once()

    def test_save(self, mock_deps):
        """Test save"""
        repo = MagicMock()
        with patch('aiEnrich.dataExtractor.validateResult'):
            _save(repo, 1, {'salary': '100k', 'required_technologies': 'T', 'optional_technologies': 'O', 'modality': 'REMOTE'})
            repo.update_enrichment.assert_called_once_with(1, '100k', 'T', 'O', 'REMOTE')
