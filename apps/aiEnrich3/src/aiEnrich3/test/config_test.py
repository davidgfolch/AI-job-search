import os
import pytest
from unittest.mock import patch
from aiEnrich3.config import get_input_max_len, get_batch_size

@pytest.mark.parametrize("env_val, expected", [
    ("5000", 5000),
    (None, 10000),
])
def test_get_input_max_len(env_val, expected):
    with patch.dict(os.environ, {"ENRICH_INPUT_MAX_LEN": env_val} if env_val else {}, clear=True):
        assert get_input_max_len() == expected

@pytest.mark.parametrize("env_val, expected", [
    ("2", 2),
    (None, 4),
])
def test_get_batch_size(env_val, expected):
    with patch.dict(os.environ, {"ENRICH_MAX_CONCURRENCY": env_val} if env_val else {}, clear=True):
        assert get_batch_size() == expected
