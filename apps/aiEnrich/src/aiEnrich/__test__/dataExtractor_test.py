import pytest
from unittest.mock import patch, MagicMock

from ..dataExtractor import (
    dataExtractor, save, getJobIdsList, DataExtractor
)


class TestDataExtractor:
    @patch('aiEnrich.dataExtractor.MysqlUtil')
    def test_data_extractor_no_jobs(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.count.return_value = 0
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        result = dataExtractor()
        assert result == 0

    @patch('aiEnrich.dataExtractor.MysqlUtil')
    @patch('aiEnrich.dataExtractor.DataExtractor')
    @patch('aiEnrich.dataExtractor.getJobIdsList')
    def test_data_extractor_success(self, mock_get_job_ids, mock_data_extractor_class, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.count.return_value = 2
        mock_mysql.fetchOne.return_value = (1, 'Test Job', 'Job description', 'Test Company')
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        mock_get_job_ids.return_value = [1, 2]
        
        mock_crew = MagicMock()
        mock_crew_output = MagicMock()
        mock_crew_output.raw = '{"salary": "50000", "required_technologies": "Python"}'
        mock_crew.kickoff.return_value = mock_crew_output
        mock_data_extractor_class.return_value.crew.return_value = mock_crew
        
        with patch('aiEnrich.dataExtractor.combineTaskResults', return_value={'salary': '50000', 'required_technologies': 'Python'}), \
             patch('aiEnrich.dataExtractor.save'), \
             patch('aiEnrich.dataExtractor.mapJob', return_value=('Test Job', 'Test Company', 'Job description')), \
             patch('aiEnrich.dataExtractor.printJob'), \
             patch('aiEnrich.dataExtractor.printHR'), \
             patch('aiEnrich.dataExtractor.footer'), \
             patch('aiEnrich.dataExtractor.StopWatch'):
            
            result = dataExtractor()
            assert result == 2

    @patch('aiEnrich.dataExtractor.MysqlUtil')
    @patch('aiEnrich.dataExtractor.DataExtractor')
    @patch('aiEnrich.dataExtractor.getJobIdsList')
    def test_data_extractor_job_not_found(self, mock_get_job_ids, mock_data_extractor_class, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.count.return_value = 1
        mock_mysql.fetchOne.return_value = None  # Job not found
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        mock_get_job_ids.return_value = [1]
        
        mock_crew = MagicMock()
        mock_data_extractor_class.return_value.crew.return_value = mock_crew
        
        with patch('aiEnrich.dataExtractor.printHR'), \
             patch('aiEnrich.dataExtractor.footer'), \
             patch('aiEnrich.dataExtractor.StopWatch'):
            
            result = dataExtractor()
            assert result == 1
            # Crew should not be called when job is not found
            mock_crew.kickoff.assert_not_called()

    @patch('aiEnrich.dataExtractor.MysqlUtil')
    @patch('aiEnrich.dataExtractor.DataExtractor')
    @patch('aiEnrich.dataExtractor.getJobIdsList')
    def test_data_extractor_exception_handling(self, mock_get_job_ids, mock_data_extractor_class, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.count.return_value = 1
        mock_mysql.fetchOne.return_value = (1, 'Test Job', 'Job description', 'Test Company')
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        mock_get_job_ids.return_value = [1]
        
        mock_crew = MagicMock()
        mock_crew.kickoff.side_effect = Exception("Processing error")
        mock_data_extractor_class.return_value.crew.return_value = mock_crew
        
        with patch('aiEnrich.dataExtractor.saveError') as mock_save_error, \
             patch('aiEnrich.dataExtractor.mapJob', return_value=('Test Job', 'Test Company', 'Job description')), \
             patch('aiEnrich.dataExtractor.printJob'), \
             patch('aiEnrich.dataExtractor.printHR'), \
             patch('aiEnrich.dataExtractor.footer'), \
             patch('aiEnrich.dataExtractor.StopWatch'):
            
            result = dataExtractor()
            assert result == 1
            mock_save_error.assert_called_once()

    def test_save(self):
        mock_mysql = MagicMock()
        result = {
            'salary': '50000',
            'required_technologies': 'Python,Django',
            'optional_technologies': 'Flask'
        }
        
        with patch('aiEnrich.dataExtractor.validateResult'), \
             patch('aiEnrich.dataExtractor.maxLen', return_value=('50000', 'Python,Django', 'Flask', 1)), \
             patch('aiEnrich.dataExtractor.emptyToNone', return_value=('50000', 'Python,Django', 'Flask', 1)):
            
            save(mock_mysql, 1, 'Test Company', result)
            mock_mysql.updateFromAI.assert_called_once()

    def test_get_job_ids_list(self):
        mock_mysql = MagicMock()
        mock_mysql.fetchAll.return_value = [(1,), (2,), (3,)]
        
        with patch('aiEnrich.dataExtractor.yellow'):
            result = getJobIdsList(mock_mysql)
            assert result == [1, 2, 3]

    def test_data_extractor_class_initialization(self):
        extractor = DataExtractor()
        # The config files are loaded as dictionaries, not file paths
        assert isinstance(extractor.agents_config, dict)
        assert isinstance(extractor.tasks_config, dict)

    @patch('aiEnrich.dataExtractor.Agent')
    @patch('aiEnrich.dataExtractor.getEnv')
    def test_extractor_agent(self, mock_get_env, mock_agent):
        mock_get_env.return_value = '300'
        extractor = DataExtractor()
        extractor.agents_config = {'extractor_agent': {'role': 'Data Extractor'}}
        
        agent = extractor.extractor_agent()
        mock_agent.assert_called_once()

    @patch('aiEnrich.dataExtractor.Task')
    def test_extractor_task(self, mock_task):
        extractor = DataExtractor()
        extractor.tasks_config = {'extractor_task': {'description': 'Extract data'}}
        
        task = extractor.extractor_task()
        mock_task.assert_called_once()

    @patch('aiEnrich.dataExtractor.Crew')
    def test_extractor_crew(self, mock_crew):
        extractor = DataExtractor()
        
        with patch.object(extractor, 'extractor_agent', return_value=MagicMock()), \
             patch.object(extractor, 'extractor_task', return_value=MagicMock()):
            
            crew = extractor.crew()
            mock_crew.assert_called_once()