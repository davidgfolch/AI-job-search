import pytest
from unittest.mock import MagicMock, patch, mock_open
from commonlib.cv_loader import CVLoader, extractTextFromPDF
import commonlib.cv_loader

class TestCVLoader:
    
    @patch("commonlib.cv_loader.pdfplumber")
    def test_extractTextFromPDF(self, mock_pdfplumber):
        # Setup mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]
        
        mock_page.extract_text.return_value = "Page 1 Text"
        mock_page.extract_tables.return_value = [] # No tables for simplicity
        
        # Execute
        result = extractTextFromPDF("dummy.pdf")
        
        # Verify
        assert "Page 1 Text" in result
        mock_pdfplumber.open.assert_called_with("dummy.pdf")

    @patch("commonlib.cv_loader.pd")
    @patch("commonlib.cv_loader.pdfplumber")
    def test_extractTextFromPDF_with_tables(self, mock_pdfplumber, mock_pd):
        # Setup mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]
        
        mock_page.extract_text.return_value = "Content"
        # Table format: list of lists. First row headers.
        mock_page.extract_tables.return_value = [
            [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]]
        ]
        
        # Mock DataFrame
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df
        mock_df.to_markdown.return_value = "| Header1 | Header2 |\n|---|---|\n| Row1Col1 | Row1Col2 |"
        
        # Execute
        result = extractTextFromPDF("dummy.pdf")
        
        # Verify
        assert "Content" in result
        assert "| Header1 | Header2 |" in result
        mock_pd.DataFrame.assert_called()
        mock_df.to_markdown.assert_called_with(index=False)

    @patch("commonlib.cv_loader.Path")
    def test_load_cv_content_disabled(self, mock_path):
        loader = CVLoader(enabled=False)
        assert loader.load_cv_content() is False

    @patch("commonlib.cv_loader.Path")
    def test_load_cv_content_cached_content(self, mock_path):
        loader = CVLoader()
        loader.cv_content = "Already Loaded"
        assert loader.load_cv_content() is True

    @patch("commonlib.cv_loader.Path")
    def test_load_cv_content_not_found(self, mock_path):
        loader = CVLoader(cv_location="missing.txt")
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        # Mocking exists to return False for both "missing.txt" and "missing.txt" (as txt check)
        # implementation creates two Path objects.
        # if not filePath.exists() and not filePathTxt.exists():
        mock_path_instance.exists.return_value = False
        
        assert loader.load_cv_content() is False

    @patch("commonlib.cv_loader.Path")
    @patch("builtins.open", new_callable=mock_open, read_data="File Content")
    def test_load_cv_content_txt_success(self, mock_file, mock_path):
        loader = CVLoader(cv_location="cv.txt")
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        # Simulate txt exists
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix.lower.return_value = '.txt'
        
        # Also need to handle "filePathTxt" exists check if we fall through
        # But if fileExtension != '.pdf' it goes to elif filePathTxt.exists()
        # So we need to ensure the sequence of mocked exists calls works.
        # OR implementation uses `if fileExtension == '.pdf'... elif filePathTxt.exists()`
        # We need `filePathTxt.exists()` to be True.
        
        assert loader.load_cv_content() is True
        assert loader.get_content() == "File Content"

    @patch("commonlib.cv_loader.Path")
    @patch("commonlib.cv_loader.extractTextFromPDF")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_cv_content_pdf_success(self, mock_file, mock_extract, mock_path):
        loader = CVLoader(cv_location="cv.pdf")
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        # Simulate pdf exists
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix.lower.return_value = '.pdf'
        # filePathTxt.exists() should simply be ignored inside the if block except for the check?
        # impl: `if fileExtension == '.pdf' and not filePathTxt.exists():`
        # So we need `filePathTxt.exists()` to be False to trigger extraction.
        
        # We need to control `exists` return values for different instances.
        # Since mock_path returns the same instance mock_path_instance every time,
        # we can use side_effect on exists.
        # Calls:
        # 1. filePath.exists() (True - allow proceed)
        # 2. filePathTxt.exists() (False - allow proceed)
        # 3. filePathTxt.exists() (False - inside if condition)
        
        mock_path_instance.exists.side_effect = [True, False, False]
        
        mock_extract.return_value = "PDF Content"
        
        assert loader.load_cv_content() is True
        assert loader.get_content() == "PDF Content"
        mock_file.assert_called_with('cv.txt', 'w', encoding='utf-8')

    @patch("commonlib.cv_loader.Path")
    def test_load_cv_content_empty(self, mock_path):
        with patch("builtins.open", mock_open(read_data="   ")):
            loader = CVLoader(cv_location="empty.txt")
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.exists.return_value = True
            
            assert loader.load_cv_content() is False

    @patch("commonlib.cv_loader.Path")
    def test_load_cv_content_exception(self, mock_path):
        loader = CVLoader()
        mock_path.side_effect = Exception("Boom")
        assert loader.load_cv_content() is False
