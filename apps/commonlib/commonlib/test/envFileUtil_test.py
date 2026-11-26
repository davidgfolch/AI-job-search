import os
from unittest.mock import patch

import pytest

from commonlib.envFileUtil import getEnvFile


@pytest.mark.parametrize("file_val, expected", [
    ('openrouter', 'openrouter'), ('', ''), (None, 'from-shell'),
])
def test_getEnvFile_prefers_file_over_process_env(file_val, expected):
    values = {'KEY': file_val} if file_val is not None else {}
    with patch('commonlib.envFileUtil.ENV_PATH') as env_path, \
         patch('commonlib.envFileUtil.ENV_LOCAL_PATH') as local_path, \
         patch('commonlib.envFileUtil.ENV_SECRETS_PATH') as secrets_path, \
         patch('commonlib.envFileUtil.dotenv_values', return_value=values), \
         patch.dict(os.environ, {'KEY': 'from-shell'}):
        env_path.exists.return_value, local_path.exists.return_value, secrets_path.exists.return_value = True, False, False
        assert getEnvFile('KEY', 'default') == expected


def test_getEnvFile_secrets_win_over_main_file():
    with patch('commonlib.envFileUtil.ENV_PATH') as env_path, \
         patch('commonlib.envFileUtil.ENV_LOCAL_PATH') as local_path, \
         patch('commonlib.envFileUtil.ENV_SECRETS_PATH') as secrets_path, \
         patch('commonlib.envFileUtil.dotenv_values', side_effect=[{'KEY': 'file'}, {'KEY': 'local'}, {'KEY': 'secret'}]) as values:
        env_path.exists.return_value, local_path.exists.return_value, secrets_path.exists.return_value = True, True, True
        assert getEnvFile('KEY', 'default') == 'secret'
        assert values.call_count == 3


def test_getEnvFile_uses_default_when_absent():
    with patch('commonlib.envFileUtil.ENV_PATH') as env_path, \
         patch('commonlib.envFileUtil.ENV_LOCAL_PATH') as local_path, \
         patch('commonlib.envFileUtil.ENV_SECRETS_PATH') as secrets_path, \
         patch('commonlib.envFileUtil.dotenv_values', return_value={}), \
         patch.dict(os.environ, {}, clear=True):
        env_path.exists.return_value, local_path.exists.return_value, secrets_path.exists.return_value = True, True, False
        assert getEnvFile('MISSING_KEY', 'default') == 'default'


def test_getEnvFile_local_wins_over_main_file():
    with patch('commonlib.envFileUtil.ENV_PATH') as env_path, \
         patch('commonlib.envFileUtil.ENV_LOCAL_PATH') as local_path, \
         patch('commonlib.envFileUtil.ENV_SECRETS_PATH') as secrets_path, \
         patch('commonlib.envFileUtil.dotenv_values', side_effect=[{'KEY': 'file'}, {'KEY': 'local'}, {}]) as values:
        env_path.exists.return_value, local_path.exists.return_value, secrets_path.exists.return_value = True, True, True
        assert getEnvFile('KEY', 'default') == 'local'
        assert values.call_count == 3
