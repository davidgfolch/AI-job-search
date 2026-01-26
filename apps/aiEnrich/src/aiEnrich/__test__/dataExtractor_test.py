import pytest
from unittest.mock import patch, MagicMock
from ..dataExtractor import dataExtractor, save, DataExtractor, getJobIdsList

@pytest.fixture
def mock_deps():
    with patch('aiEnrich.dataExtractor.MysqlUtil') as mysql_util, \
         patch('aiEnrich.dataExtractor.save') as save_chk, \
         patch('aiEnrich.dataExtractor.printJob'), patch('aiEnrich.dataExtractor.printHR'), \
         patch('aiEnrich.dataExtractor.footer'), patch('aiEnrich.dataExtractor.StopWatch'), \
         patch('aiEnrich.dataExtractor.combineTaskResults'), patch('aiEnrich.dataExtractor.mapJob'):
        
        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql
        yield {'mysql': mysql, 'save': save_chk}

class TestDataExtractor:
    
    @patch('aiEnrich.dataExtractor.getJobIdsList', return_value=[1])
    @patch('aiEnrich.dataExtractor.DataExtractor')
    def test_extractor_success(self, mock_cls, mock_ids, mock_deps):
        """Test success"""
        mock_deps['mysql'].count.return_value = 1
        mock_deps['mysql'].fetchOne.return_value = (1, 'Job', 'Desc', 'Comp')
        
        crew_mock = MagicMock()
        mock_cls.return_value.crew.return_value = crew_mock
        
        with patch('aiEnrich.dataExtractor.combineTaskResults', return_value={'salary': '100k'}), \
             patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            assert dataExtractor() == 1
            mock_deps['save'].assert_called()

    def test_save(self, mock_deps):
        """Test save"""
        with patch('aiEnrich.dataExtractor.validateResult'), \
             patch('aiEnrich.dataExtractor.maxLen', return_value=('100k', 'T', 'O', 1)), \
             patch('aiEnrich.dataExtractor.emptyToNone', return_value=('100k', 'T', 'O', 1)):
            save(mock_deps['mysql'], 1, 'Comp', {'salary': '100k'})
            mock_deps['mysql'].updateFromAI.assert_called_once()