"""Tests for filter_parser utility module."""
import pytest
from utils.filter_parser import (
    BOOLEAN_FILTER_KEYS,
    JOB_BOOLEAN_KEYS,
    extract_boolean_filters,
    extract_filter_params,
)


class TestExtractBooleanFilters:
    """Tests for extract_boolean_filters function."""

    def test_extract_all_boolean_keys(self):
        """Test extracting all boolean filter keys from a dictionary."""
        filters = {
            'flagged': True,
            'like': False,
            'ignored': True,
            'seen': True,
            'applied': False,
            'discarded': True,
            'closed': False,
            'interview_rh': True,
            'interview': False,
            'interview_tech': True,
            'interview_technical_test': False,
            'interview_technical_test_done': True,
            'ai_enriched': False,
            'easy_apply': True,
            'search': 'python',  # Non-boolean should not be included
        }

        result = extract_boolean_filters(filters)

        expected = {
            'flagged': True,
            'like': False,
            'ignored': True,
            'seen': True,
            'applied': False,
            'discarded': True,
            'closed': False,
            'interview_rh': True,
            'interview': False,
            'interview_tech': True,
            'interview_technical_test': False,
            'interview_technical_test_done': True,
            'ai_enriched': False,
            'easy_apply': True,
        }

        assert result == expected

    def test_extract_partial_boolean_filters(self):
        """Test extracting only some boolean filters."""
        filters = {
            'flagged': True,
            'applied': False,
            'search': 'python',
        }

        result = extract_boolean_filters(filters)

        assert result == {'flagged': True, 'applied': False}

    def test_extract_empty_filters(self):
        """Test extracting from empty dictionary."""
        result = extract_boolean_filters({})
        assert result == {}

    def test_extract_with_custom_keys(self):
        """Test extracting with custom key list."""
        filters = {
            'flagged': True,
            'like': False,
            'custom': True,
        }

        result = extract_boolean_filters(filters, keys=['flagged', 'custom'])

        assert result == {'flagged': True, 'custom': True}

    def test_extract_skips_missing_keys(self):
        """Test that missing keys are simply not included."""
        filters = {
            'unknown_key': True,
        }

        result = extract_boolean_filters(filters)
        assert result == {}


class TestExtractFilterParams:
    """Tests for extract_filter_params function."""

    def test_extract_all_params(self):
        """Test extracting all filter parameters."""
        filters = {
            'search': 'python',
            'status': 'applied,interviewing',
            'not_status': 'discarded',
            'days_old': 7,
            'salary': '100k',
            'sql_filter': 'salary > 1000',
            'flagged': True,
            'applied': False,
            'ids': [1, 2, 3],
            'created_after': '2023-01-01T00:00:00',
        }

        result = extract_filter_params(filters)

        assert result['search'] == 'python'
        assert result['status'] == 'applied,interviewing'
        assert result['not_status'] == 'discarded'
        assert result['days_old'] == 7
        assert result['salary'] == '100k'
        assert result['sql_filter'] == 'salary > 1000'
        assert result['ids'] == [1, 2, 3]
        assert result['created_after'] == '2023-01-01T00:00:00'
        assert isinstance(result['boolean_filters'], dict)
        assert result['boolean_filters']['flagged'] is True
        assert result['boolean_filters']['applied'] is False

    def test_extract_empty_filters(self):
        """Test extracting from empty dictionary."""
        result = extract_filter_params({})
        assert result['search'] is None
        assert result['boolean_filters'] == {}

    def test_extract_with_none_values(self):
        """Test that None values are preserved if key exists."""
        filters = {
            'search': None,
            'flagged': None,
        }

        result = extract_filter_params(filters)
        assert result['search'] is None
        # None values are included if the key exists (not filtered out)
        assert result['boolean_filters'] == {'flagged': None}


class TestBooleanFilterKeys:
    """Tests for BOOLEAN_FILTER_KEYS constant."""

    def test_boolean_keys_exists(self):
        """Test that BOOLEAN_FILTER_KEYS is defined."""
        assert BOOLEAN_FILTER_KEYS is not None
        assert isinstance(BOOLEAN_FILTER_KEYS, list)
        assert len(BOOLEAN_FILTER_KEYS) > 0

    def test_boolean_keys_consistent(self):
        """Test that all boolean keys are valid field names."""
        for key in BOOLEAN_FILTER_KEYS:
            assert isinstance(key, str)
            # Check key is in expected format (snake_case)
            assert key.replace('_', '').isalpha(), f"Key '{key}' should only contain letters and underscores"


class TestJobBooleanKeys:
    """Tests for JOB_BOOLEAN_KEYS backward compatibility alias."""

    def test_job_boolean_keys_exists(self):
        """Test that JOB_BOOLEAN_KEYS is defined (backward compatibility)."""
        assert JOB_BOOLEAN_KEYS is not None
        assert isinstance(JOB_BOOLEAN_KEYS, list)

    def test_job_boolean_keys_is_alias(self):
        """Test that JOB_BOOLEAN_KEYS is the same as BOOLEAN_FILTER_KEYS."""
        assert JOB_BOOLEAN_KEYS is BOOLEAN_FILTER_KEYS

    @pytest.mark.parametrize("key", [
        'flagged', 'like', 'ignored', 'seen', 'applied', 'discarded',
        'closed', 'interview_rh', 'interview', 'interview_tech'
    ])
    def test_specific_keys_present(self, key):
        """Test that specific keys are present in JOB_BOOLEAN_KEYS."""
        assert key in JOB_BOOLEAN_KEYS
