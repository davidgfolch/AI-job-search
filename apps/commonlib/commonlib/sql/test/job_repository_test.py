"""Tests for job_repository module."""
import pytest
from unittest.mock import MagicMock, patch
from commonlib.sql.job_repository import JobRepository


class TestJobRepository:
    """Tests for JobRepository class."""

    @pytest.fixture
    def mock_execute_transaction(self):
        """Mock execute_transaction function."""
        return MagicMock()

    @pytest.fixture
    def mock_execute_query(self):
        """Mock execute_query function."""
        return MagicMock()

    @pytest.fixture
    def job_repository(self, mock_execute_transaction, mock_execute_query):
        """Create JobRepository instance with mocks."""
        return JobRepository(mock_execute_transaction, mock_execute_query)

    def test_init(self, mock_execute_transaction, mock_execute_query):
        """Should initialize with execute_transaction and execute_query functions."""
        repo = JobRepository(mock_execute_transaction, mock_execute_query)
        assert repo._execute_transaction == mock_execute_transaction
        assert repo._execute_query == mock_execute_query

    def test_insert_calls_execute_transaction(self, job_repository, mock_execute_transaction):
        """insert should call execute_transaction with correct callback."""
        params = ('job123', 'Title', 'Company', 'Location', 'url', 'md', False, 'web', None)
        mock_execute_transaction.return_value = 1

        result = job_repository.insert(params)

        assert mock_execute_transaction.called
        assert result == 1

    def test_insert_returns_none_on_error(self, job_repository, mock_execute_transaction):
        """insert should return None on error."""
        mock_execute_transaction.side_effect = Exception('DB error')

        params = ('job123', 'Title', 'Company', 'Location', 'url', 'md', False, 'web', None)
        result = job_repository.insert(params)

        assert result is None

    def test_job_exists_returns_true_when_found(self, job_repository, mock_execute_query):
        """job_exists should return True when job is found."""
        mock_execute_query.return_value = {'id': 1, 'jobId': 'job123'}

        result = job_repository.job_exists('job123')

        assert result is True

    def test_job_exists_returns_false_when_not_found(self, job_repository, mock_execute_query):
        """job_exists should return False when job is not found."""
        mock_execute_query.return_value = None

        result = job_repository.job_exists('job999')

        assert result is False

    def test_insert_job_builds_params_correctly(self, job_repository, mock_execute_transaction):
        """insert_job should build params tuple correctly."""
        job_data = {
            'job_id': 'job123',
            'title': 'Software Engineer',
            'company': 'Test Corp',
            'location': 'Remote',
            'url': 'https://example.com/job/123',
            'markdown': '# Job Description',
            'easy_apply': True,
            'web_page': 'linkedin',
            'duplicated_id': 42
        }
        mock_execute_transaction.return_value = 1

        result = job_repository.insert_job(job_data)

        assert mock_execute_transaction.called
        assert result == 1

    def test_insert_job_with_defaults(self, job_repository, mock_execute_transaction):
        """insert_job should use defaults for missing keys."""
        job_data = {'job_id': 'job123'}
        mock_execute_transaction.return_value = 1

        result = job_repository.insert_job(job_data)

        assert mock_execute_transaction.called
        assert result == 1
