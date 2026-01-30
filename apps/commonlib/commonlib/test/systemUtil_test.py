import pytest
import platform
import os
from unittest.mock import patch, mock_open
from commonlib.systemUtil import isDocker, isMacOS, isWindowsOS, isLinuxOS

class TestSystemUtil:
    
    def test_isDocker_env_file(self):
        with patch('commonlib.systemUtil.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            assert isDocker() is True
            mock_exists.assert_called_with('/.dockerenv')
            
    def test_isDocker_cgroup(self):
        with patch('commonlib.systemUtil.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            with patch('builtins.open', mock_open(read_data='docker')):
                assert isDocker() is True
                
    def test_isDocker_false(self):
         with patch('commonlib.systemUtil.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            with patch('builtins.open', new_callable=mock_open) as mock_file:
                mock_file.side_effect = FileNotFoundError
                assert isDocker() is False

    @patch('commonlib.systemUtil.platform.system')
    def test_isMacOS(self, mock_system):
        mock_system.return_value = 'Darwin'
        assert isMacOS() is True
        mock_system.return_value = 'Windows'
        assert isMacOS() is False

    @patch('commonlib.systemUtil.platform.system')
    def test_isWindowsOS(self, mock_system):
        mock_system.return_value = 'Windows'
        assert isWindowsOS() is True
        mock_system.return_value = 'Linux'
        assert isWindowsOS() is False

    @patch('commonlib.systemUtil.platform.system')
    def test_isLinuxOS(self, mock_system):
        mock_system.return_value = 'Linux'
        assert isLinuxOS() is True
        mock_system.return_value = 'Darwin'
        assert isLinuxOS() is False
