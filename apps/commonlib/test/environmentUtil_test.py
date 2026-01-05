import pytest
from unittest.mock import patch
import os
from commonlib.environmentUtil import getEnv, getEnvBool

class TestEnvironmentFunctions:
    def test_get_env_existing_var(self):
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = getEnv('TEST_VAR')
            assert result == 'test_value'

    def test_get_env_non_existing_var_with_default(self):
        result = getEnv('NON_EXISTING_VAR', 'default_value')
        assert result == 'default_value'

    def test_get_env_non_existing_var_no_default(self):
        result = getEnv('NON_EXISTING_VAR')
        assert result is None

    def test_get_env_bool_true_values(self):
        true_values = ['true', 'True', 'TRUE']
        for value in true_values:
            with patch.dict(os.environ, {'TEST_BOOL': value}):
                result = getEnvBool('TEST_BOOL')
                assert result is True, f"Expected True for value '{value}', got {result}"

    def test_get_env_bool_false_values(self):
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', '']
        for value in false_values:
            with patch.dict(os.environ, {'TEST_BOOL': value}):
                result = getEnvBool('TEST_BOOL')
                assert result is False

    def test_get_env_bool_default(self):
        result = getEnvBool('NON_EXISTING_BOOL', True)
        assert result is True
