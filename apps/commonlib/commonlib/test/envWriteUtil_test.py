import errno
import pytest
from pathlib import Path
from unittest.mock import patch
from dotenv import dotenv_values, set_key as real_set_key
from commonlib.envWriteUtil import set_keys


def _busy_for_mount(env_file):
    def busy(path, key, value, **kwargs):
        if Path(path) == env_file:
            raise OSError(errno.EBUSY, 'Device or resource busy')
        return real_set_key(path, key, value, **kwargs)
    return busy


class TestEnvWriteUtil:
    def test_set_keys_writes_existing_file(self, tmp_path):
        env_file = tmp_path / '.env'
        env_file.write_text('OLD=old\nKEEP=keep\n', encoding='utf-8')
        set_keys(env_file, {'OLD': 'new', 'NEW': 'val'})
        values = dotenv_values(env_file)
        assert values['OLD'] == 'new'
        assert values['NEW'] == 'val'
        assert values['KEEP'] == 'keep'

    def test_set_keys_rewrites_bind_mounted_file_in_place(self, tmp_path):
        env_file = tmp_path / '.env'
        env_file.write_text('OLD=old\nKEEP=keep\n', encoding='utf-8')
        with patch('commonlib.envWriteUtil.set_key', side_effect=_busy_for_mount(env_file)):
            set_keys(env_file, {'OLD': 'new'})
        values = dotenv_values(env_file)
        assert values['OLD'] == 'new'
        assert values['KEEP'] == 'keep'

    def test_set_keys_bind_mount_eperm_falls_back(self, tmp_path):
        env_file = tmp_path / '.env'
        env_file.write_text('K=old\n', encoding='utf-8')
        def busy(path, key, value, **kwargs):
            if Path(path) == env_file:
                raise OSError(errno.EPERM, 'Operation not permitted')
            return real_set_key(path, key, value, **kwargs)
        with patch('commonlib.envWriteUtil.set_key', side_effect=busy):
            set_keys(env_file, {'K': 'new'})
        assert dotenv_values(env_file)['K'] == 'new'

    def test_set_keys_propagates_other_write_errors(self, tmp_path):
        env_file = tmp_path / '.env'
        env_file.write_text('K=old\n', encoding='utf-8')
        with patch('commonlib.envWriteUtil.set_key', side_effect=OSError(errno.EACCES, 'Permission denied')):
            with pytest.raises(OSError):
                set_keys(env_file, {'K': 'new'})
        assert dotenv_values(env_file)['K'] == 'old'
