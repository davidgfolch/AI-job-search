import pytest
from unittest.mock import MagicMock, patch, mock_open
from commonlib.cv_loader import CVLoader

@patch("commonlib.cv_loader.Path")
@patch("builtins.open", new_callable=mock_open, read_data="Mock CV Content")
def test_load_cv_content_txt_exists(mock_file, mock_path):
    # Setup
    mock_path_obj = MagicMock()
    mock_path.return_value = mock_path_obj
    
    # Simulate .txt exists
    mock_path_obj.exists.side_effect = [False, True] # pdf exists? txt exists? 
    # Wait, implementation checks:
    # filePath = Path(cv_location)
    # filePathTxt = Path(cv_location_txt)
    # if not filePath.exists() and not filePathTxt.exists(): return False
    
    # We need to mock Path instantiation.
    # It calls Path(CV_LOCATION) and Path(cvLocationTxt)
    
    loader = CVLoader(cv_location="cv.pdf")
    
    # We need to be careful with how Path is mocked since it's instantiated twice
    # Easier to mock exists on the instances returned
    
    path_pdf = MagicMock()
    path_txt = MagicMock()
    mock_path.side_effect = [path_pdf, path_txt, path_pdf, path_txt] # for init and inside method
    
    path_pdf.suffix = '.pdf'
    path_pdf.exists.return_value = False
    path_txt.exists.return_value = True
    
    assert loader.load_cv_content() is True
    assert loader.get_content() == "Mock CV Content"

@patch("commonlib.cv_loader.Path")
@patch("commonlib.cv_loader.extractTextFromPDF")
@patch("builtins.open", new_callable=mock_open)
def test_load_cv_content_pdf_extraction(mock_file, mock_extract, mock_path):
    loader = CVLoader(cv_location="cv.pdf")
    
    path_pdf = MagicMock()
    path_txt = MagicMock()
    mock_path.side_effect = [path_pdf, path_txt] 
    
    path_pdf.exists.return_value = True
    path_pdf.suffix.lower.return_value = '.pdf'
    path_txt.exists.return_value = False
    
    mock_extract.return_value = "Extracted PDF Content"
    
    assert loader.load_cv_content() is True
    assert loader.get_content() == "Extracted PDF Content"
    mock_extract.assert_called_once_with("cv.pdf")
    # Verify it saves cache
    mock_file.assert_called_with('cv.txt', 'w', encoding='utf-8')
