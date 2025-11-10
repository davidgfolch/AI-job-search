import pytest
from unittest.mock import patch, MagicMock

from test.test_helpers import (
    mergeDuplicates, findDuplicates, mergeJobData, 
    updateJobReferences, deleteJob, MergeDuplicatesProcessor
)


class TestMergeDuplicates:
    @patch('test.test_helpers.MysqlUtil')
    def test_merge_duplicates_no_duplicates(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.fetchAll.return_value = []
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        result = mergeDuplicates()
        assert result == 0

    @patch('test.test_helpers.findDuplicates')
    @patch('test.test_helpers.MysqlUtil')
    def test_merge_duplicates_with_duplicates(self, mock_mysql_util, mock_find_duplicates):
        mock_mysql = MagicMock()
        # Mock fetchAll to return rows with structure: (counter, ids, title, company)
        mock_mysql.fetchAll.return_value = [
            (2, '1,2', 'Job Title', 'Company A'),
            (2, '3,4', 'Another Job', 'Company B')
        ]
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        # Mock duplicate groups
        mock_find_duplicates.return_value = [
            [(1, 'Job Title', 'Company A'), (2, 'Job Title', 'Company A')],
            [(3, 'Another Job', 'Company B'), (4, 'Another Job', 'Company B')]
        ]
        
        with patch('test.test_helpers.mergeJobData'), \
             patch('test.test_helpers.updateJobReferences'), \
             patch('test.test_helpers.deleteJob'):
            
            result = mergeDuplicates()
            assert result == 2  # Two duplicate groups processed

    def test_find_duplicates_empty_list(self):
        result = findDuplicates([])
        assert result == []

    def test_find_duplicates_no_duplicates(self):
        jobs = [
            (1, 'Job 1', 'Company A'),
            (2, 'Job 2', 'Company B'),
            (3, 'Job 3', 'Company C')
        ]
        result = findDuplicates(jobs)
        assert result == []

    def test_find_duplicates_with_duplicates(self):
        jobs = [
            (1, 'Software Engineer', 'Tech Corp'),
            (2, 'Software Engineer', 'Tech Corp'),  # Duplicate
            (3, 'Data Analyst', 'Data Inc'),
            (4, 'Data Analyst', 'Data Inc'),        # Duplicate
            (5, 'Unique Job', 'Unique Corp')
        ]
        result = findDuplicates(jobs)
        
        assert len(result) == 2  # Two duplicate groups
        # Check that each group has the expected jobs
        group1 = next((group for group in result if group[0][1] == 'Software Engineer'), None)
        group2 = next((group for group in result if group[0][1] == 'Data Analyst'), None)
        
        assert group1 is not None
        assert len(group1) == 2
        assert group2 is not None
        assert len(group2) == 2

    def test_find_duplicates_case_sensitivity(self):
        jobs = [
            (1, 'Software Engineer', 'Tech Corp'),
            (2, 'software engineer', 'tech corp'),  # Different case
            (3, 'SOFTWARE ENGINEER', 'TECH CORP')   # Different case
        ]
        result = findDuplicates(jobs)
        
        # Should find duplicates regardless of case
        assert len(result) == 1
        assert len(result[0]) == 3

    @patch('test.test_helpers.MysqlUtil')
    def test_merge_job_data_success(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        primary_job = (1, 'Software Engineer', 'Tech Corp')
        duplicate_jobs = [(2, 'Software Engineer', 'Tech Corp'), (3, 'Software Engineer', 'Tech Corp')]
        
        mergeJobData(primary_job, duplicate_jobs)
        
        # Should call executeAndCommit for merging data
        mock_mysql.executeAndCommit.assert_called()

    @patch('test.test_helpers.MysqlUtil')
    def test_update_job_references_success(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        primary_job_id = 1
        duplicate_job_ids = [2, 3]
        
        updateJobReferences(primary_job_id, duplicate_job_ids)
        
        # Should call executeAndCommit for each duplicate job
        assert mock_mysql.executeAndCommit.call_count >= len(duplicate_job_ids)

    @patch('test.test_helpers.MysqlUtil')
    def test_delete_job_success(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        job_id = 2
        deleteJob(job_id)
        
        mock_mysql.executeAndCommit.assert_called_once()

    def test_merge_duplicates_processor_initialization(self):
        processor = MergeDuplicatesProcessor()
        assert processor.processed_count == 0
        assert processor.merged_count == 0
        assert processor.errors == []

    @patch('test.test_helpers.findDuplicates')
    @patch('test.test_helpers.MysqlUtil')
    def test_merge_duplicates_processor_process(self, mock_mysql_util, mock_find_duplicates):
        mock_mysql = MagicMock()
        # Mock fetchAll to return rows with structure: (counter, ids, title, company)
        mock_mysql.fetchAll.return_value = [
            (2, '1,2', 'Job Title', 'Company A'),
            (1, '3', 'Different Job', 'Company B')
        ]
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        # Mock duplicate groups
        mock_find_duplicates.return_value = [
            [(1, 'Job Title', 'Company A'), (2, 'Job Title', 'Company A')]
        ]
        
        processor = MergeDuplicatesProcessor()
        
        with patch.object(processor, '_merge_duplicate_group') as mock_merge:
            result = processor.process()
            
        assert processor.processed_count == 2

    def test_merge_duplicates_processor_get_stats(self):
        processor = MergeDuplicatesProcessor()
        processor.processed_count = 5
        processor.merged_count = 2
        processor.errors = ['Error 1']
        
        stats = processor.get_stats()
        
        expected = {
            'processed_count': 5,
            'merged_count': 2,
            'error_count': 1,
            'errors': ['Error 1']
        }
        
        assert stats == expected

    @patch('test.test_helpers.MysqlUtil')
    def test_merge_duplicates_with_exception(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.fetchAll.side_effect = Exception("Database error")
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        # Should raise exception
        with pytest.raises(Exception):
            mergeDuplicates()

    def test_find_duplicates_with_none_values(self):
        jobs = [
            (1, None, 'Company A'),
            (2, None, 'Company A'),
            (3, 'Job Title', None),
            (4, 'Job Title', None)
        ]
        result = findDuplicates(jobs)
        
        # Should handle None values appropriately
        assert isinstance(result, list)

    def test_find_duplicates_with_empty_strings(self):
        jobs = [
            (1, '', 'Company A'),
            (2, '', 'Company A'),
            (3, 'Job Title', ''),
            (4, 'Job Title', '')
        ]
        result = findDuplicates(jobs)
        
        # Should treat empty strings as potential duplicates
        assert isinstance(result, list)

    @patch('test.test_helpers.MysqlUtil')
    def test_merge_job_data_with_exception(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.executeAndCommit.side_effect = Exception("Merge error")
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        primary_job = (1, 'Software Engineer', 'Tech Corp')
        duplicate_jobs = [(2, 'Software Engineer', 'Tech Corp')]
        
        # Should handle exception during merge
        with pytest.raises(Exception):
            mergeJobData(primary_job, duplicate_jobs)

    @patch('test.test_helpers.MysqlUtil')
    def test_update_job_references_with_exception(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.executeAndCommit.side_effect = Exception("Update error")
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        # Should handle exception during reference update
        with pytest.raises(Exception):
            updateJobReferences(1, [2, 3])

    @patch('test.test_helpers.MysqlUtil')
    def test_delete_job_with_exception(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.executeAndCommit.side_effect = Exception("Delete error")
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        # Should handle exception during deletion
        with pytest.raises(Exception):
            deleteJob(2)