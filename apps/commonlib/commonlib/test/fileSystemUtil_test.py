import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from commonlib.fileSystemUtil import createFolder, listFiles, getSrcPath
import os

class TestFileSystemUtil:
    
    @patch('commonlib.fileSystemUtil.Path')
    def test_createFolder(self, mock_path_class):
        # Setup
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_parent = MagicMock()
        mock_path_instance.parent = mock_parent
        
        # Execute
        filename = "path/to/file.txt"
        result = createFolder(filename)
        
        # Verify
        mock_path_class.assert_called_with(filename)
        mock_parent.mkdir.assert_called_once_with(exist_ok=True, parents=True)
        assert result == mock_path_instance

    @patch('commonlib.fileSystemUtil.os.listdir')
    @patch('commonlib.fileSystemUtil.isfile')
    @patch('commonlib.fileSystemUtil.join')
    def test_listFiles(self, mock_join, mock_isfile, mock_listdir):
        # Setup
        folder = Path("/some/folder")
        mock_listdir.return_value = ["file1.txt", "dir1", "file2.py"]
        
        # Mock isfile to return True for files and False for directories
        def isfile_side_effect(path):
            return "file" in str(path)
        mock_isfile.side_effect = isfile_side_effect
        
        # Mock join to simply concatenate for verification
        mock_join.side_effect = lambda a, b: f"{a}/{b}"
        
        # Execute
        result = listFiles(folder)
        
        # Verify
        assert "file1.txt" in result
        assert "file2.py" in result
        assert "dir1" not in result
        assert len(result) == 2
        mock_listdir.assert_called_once()

    @patch('commonlib.fileSystemUtil.os.getcwd')
    def test_getSrcPath(self, mock_getcwd):
        # Setup
        expected_path = "/current/working/dir"
        mock_getcwd.return_value = expected_path
        
        # Execute
        result = getSrcPath()
        
        # Verify
        # On windows Path might convert separators, but here we cast to str
        # We need to account that Path(str) normalization might happen.
        # But essentially it should wrap cwd.
        assert str(Path(expected_path)) == result
