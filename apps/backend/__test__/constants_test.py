import pytest
from constants import JOB_BOOLEAN_KEYS

def test_job_boolean_keys_exists():
    assert JOB_BOOLEAN_KEYS is not None
    assert isinstance(JOB_BOOLEAN_KEYS, list)

def test_job_boolean_keys_content():
    expected_keys = [
        'flagged', 'like', 'ignored', 'seen', 'applied', 'discarded', 'closed',
        'interview_rh', 'interview', 'interview_tech', 'interview_technical_test',
        'interview_technical_test_done', 'ai_enriched', 'easy_apply'
    ]
    assert JOB_BOOLEAN_KEYS == expected_keys

@pytest.mark.parametrize("key", [
    'flagged', 'like', 'ignored', 'seen', 'applied', 'discarded',
    'closed', 'interview_rh', 'interview', 'interview_tech'
])
def test_specific_keys_present(key):
    assert key in JOB_BOOLEAN_KEYS
