import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
from commonlib.environmentUtil import (
    getEnv, getEnvBool, getEnvModified, checkEnvReload,
    getEnvMultiline, getEnvByPrefix, getEnvAll, setEnv, setEnvBulk
)
import commonlib.environmentUtil as envUtil


class TestEnvironmentUtil:
    def test_getEnvModified_exists(self):
        with patch('commonlib.environmentUtil.ENV_PATH') as mock_path, \
             patch('commonlib.environmentUtil.ENV_SECRETS_PATH') as mock_sec_path:
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 12345.0
            mock_sec_path.exists.return_value = False
            assert getEnvModified() == 12345.0

    def test_getEnvModified_both_exist(self):
        with patch('commonlib.environmentUtil.ENV_PATH') as mock_path, \
             patch('commonlib.environmentUtil.ENV_SECRETS_PATH') as mock_sec_path:
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 100.0
            mock_sec_path.exists.return_value = True
            mock_sec_path.stat.return_value.st_mtime = 200.0
            assert getEnvModified() == 200.0

    def test_getEnvModified_none_exist(self):
        with patch('commonlib.environmentUtil.ENV_PATH') as mock_path, \
             patch('commonlib.environmentUtil.ENV_SECRETS_PATH') as mock_sec_path:
            mock_path.exists.return_value = False
            mock_sec_path.exists.return_value = False
            assert getEnvModified() is None

    @patch('commonlib.environmentUtil.load_dotenv')
    @patch('commonlib.environmentUtil.getEnvModified')
    def test_checkEnvReload(self, mock_get_mod, mock_load):
        envUtil.envLastModified = 100
        mock_get_mod.return_value = 200
        checkEnvReload()
        assert mock_load.call_count == 2
        assert envUtil.envLastModified == 200

    @patch('commonlib.environmentUtil.load_dotenv')
    @patch('commonlib.environmentUtil.getEnvModified')
    def test_checkEnvReload_no_change(self, mock_get_mod, mock_load):
        envUtil.envLastModified = 100
        mock_get_mod.return_value = 100
        checkEnvReload()
        mock_load.assert_not_called()

    def test_getEnvMultiline(self):
        def side_effect(key, required=False):
            mapping = {'KEY_1': 'Part1', 'KEY_2': 'Part2'}
            return mapping.get(key)
        with patch('commonlib.environmentUtil.getEnv', side_effect=side_effect):
            result = getEnvMultiline('KEY')
            assert result == 'Part1Part2'

    def test_getEnvMultiline_empty(self):
        with patch('commonlib.environmentUtil.getEnv', return_value=None):
            result = getEnvMultiline('KEY')
            assert result == ''

    def test_getEnvByPrefix(self):
        with patch.dict(os.environ, {'MYPREFIX_A': 'valA', 'MYPREFIX_B': 'valB', 'OTHER_C': 'valC'}):
            result = getEnvByPrefix('MYPREFIX_')
            assert result == {'A': 'valA', 'B': 'valB'}
            assert 'C' not in result

    def test_getEnvByPrefix_required_fail(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Required environment variables"):
                getEnvByPrefix('MISSING_', required=True)

    def test_getEnv_required_missing(self):
        with pytest.raises(ValueError, match="Required environment variable"):
            getEnv('NONEXISTENT_VAR_XYZ', required=True)

    def test_getEnvBool_true(self):
        with patch.dict(os.environ, {'MY_BOOL': 'true'}):
            assert getEnvBool('MY_BOOL') is True

    def test_getEnvBool_false(self):
        with patch.dict(os.environ, {'MY_BOOL': 'false'}):
            assert getEnvBool('MY_BOOL') is False

    def test_getEnvBool_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('MY_BOOL_MISSING', None)
            assert getEnvBool('MY_BOOL_MISSING', default=True) is True

    @patch('commonlib.environmentUtil.dotenv_values')
    def test_getEnvAll(self, mock_dotenv_values):
        def mock_dotenv(path):
            if str(path).endswith('.env.secrets.example'):
                return {'SECRET_KEY1': 'secret_default1'}
            if str(path).endswith('.env.secrets'):
                return {'SECRET_KEY1': 'secret_actual1'}
            if str(path).endswith('.env'):
                return {'KEY1': 'actual1', 'KEY3': ''}
            return {}
        mock_dotenv_values.side_effect = mock_dotenv
        with patch('commonlib.environmentUtil.ENV_PATH') as mock_env_path, \
             patch('commonlib.environmentUtil.ENV_SECRETS_EXAMPLE_PATH') as mock_seg_path, \
             patch('commonlib.environmentUtil.ENV_SECRETS_PATH') as mock_senv_path:
            mock_env_path.exists.return_value = True
            mock_env_path.__str__.return_value = '/fake/.env'
            mock_seg_path.exists.return_value = True
            mock_seg_path.__str__.return_value = '/fake/.env.secrets.example'
            mock_senv_path.exists.return_value = True
            mock_senv_path.__str__.return_value = '/fake/.env.secrets'
            result = getEnvAll()
            assert result['KEY1'] == 'actual1'
            assert result['SECRET_KEY1'] == 'secret_actual1'

    @patch('commonlib.environmentUtil.set_key')
    @patch('commonlib.environmentUtil.load_dotenv')
    @patch('commonlib.environmentUtil.getEnvModified')
    def test_setEnv_existing_file(self, mock_get_mod, mock_load, mock_set_key):
        with patch('commonlib.environmentUtil.ENV_PATH') as mock_env_path:
            mock_env_path.exists.return_value = True
            mock_env_path.__str__.return_value = '/fake/.env'
            mock_get_mod.return_value = 300
            setEnv('NEW_KEY', 'NEW_VALUE')
            mock_set_key.assert_called_once()
            mock_load.assert_called_once()

    @patch('commonlib.environmentUtil.set_key')
    @patch('commonlib.environmentUtil.load_dotenv')
    @patch('commonlib.environmentUtil.getEnvModified')
    def test_setEnv_new_file(self, mock_get_mod, mock_load, mock_set_key):
        with patch('commonlib.environmentUtil.ENV_PATH') as mock_env_path:
            mock_env_path.exists.return_value = False
            mock_get_mod.return_value = 400
            m_open = mock_open()
            with patch('builtins.open', m_open):
                setEnv('NEW_KEY', 'NEW_VALUE')
            m_open.assert_called_once()

    @patch('commonlib.environmentUtil.set_key')
    @patch('commonlib.environmentUtil.load_dotenv')
    @patch('commonlib.environmentUtil.getEnvModified')
    def test_setEnvBulk_existing_file(self, mock_get_mod, mock_load, mock_set_key):
        with patch('commonlib.environmentUtil.ENV_PATH') as mock_env_path:
            mock_env_path.exists.return_value = True
            mock_get_mod.return_value = 500
            setEnvBulk({'K1': 'V1', 'K2': 'V2'})
            assert mock_set_key.call_count == 2

    @patch('commonlib.environmentUtil.set_key')
    @patch('commonlib.environmentUtil.load_dotenv')
    @patch('commonlib.environmentUtil.getEnvModified')
    def test_setEnvBulk_new_file(self, mock_get_mod, mock_load, mock_set_key):
        with patch('commonlib.environmentUtil.ENV_PATH') as mock_env_path:
            mock_env_path.exists.return_value = False
            mock_get_mod.return_value = 600
            m_open = mock_open()
            with patch('builtins.open', m_open):
                setEnvBulk({'K1': 'V1', 'K2': 'V2'})
            m_open.assert_called_once()
