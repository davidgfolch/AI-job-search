import pytest
from unittest.mock import MagicMock, patch, mock_open
from commonlib.cv_loader import CVLoader, extractTextFromPDF


class TestCVLoader:
    @patch("commonlib.cv_loader.pdfplumber")
    def test_extractTextFromPDF(self, mock_pdfplumber):
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]
        mock_page.extract_text.return_value = "Page 1 Text"
        mock_page.extract_tables.return_value = []
        result = extractTextFromPDF("dummy.pdf")
        assert "Page 1 Text" in result

    @patch("commonlib.cv_loader.pd")
    @patch("commonlib.cv_loader.pdfplumber")
    def test_extractTextFromPDF_with_tables(self, mock_pdfplumber, mock_pd):
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]
        mock_page.extract_text.return_value = "Content"
        mock_page.extract_tables.return_value = [
            [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]]
        ]
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df
        mock_df.to_markdown.return_value = "| Header1 | Header2 |\n|---|---|"
        result = extractTextFromPDF("dummy.pdf")
        assert "Content" in result

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
        mock_path_instance.exists.return_value = False
        assert loader.load_cv_content() is False

    @patch("commonlib.cv_loader.Path")
    @patch("builtins.open", new_callable=mock_open, read_data="File Content")
    def test_load_cv_content_txt_success(self, mock_file, mock_path):
        loader = CVLoader(cv_location="cv.txt")
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix.lower.return_value = '.txt'
        assert loader.load_cv_content() is True
        assert loader.get_content() == "File Content"

    @patch("commonlib.cv_loader.Path")
    @patch("commonlib.cv_loader.extractTextFromPDF")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_cv_content_pdf_success(self, mock_file, mock_extract, mock_path):
        loader = CVLoader(cv_location="cv.pdf")
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.side_effect = [True, False, False]
        mock_path_instance.suffix.lower.return_value = '.pdf'
        mock_extract.return_value = "PDF Content"
        assert loader.load_cv_content() is True
        assert loader.get_content() == "PDF Content"

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

    @patch("commonlib.cv_loader.Path")
    def test_load_cv_content_unsupported_format(self, mock_path):
        loader = CVLoader(cv_location="cv.docx")
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix.lower.return_value = '.docx'
        assert loader.load_cv_content() is False

    @patch("commonlib.cv_loader.Path")
    @patch("commonlib.cv_loader.extractTextFromPDF")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_cv_content_pdf_save_cache_error(self, mock_file, mock_extract, mock_path):
        loader = CVLoader(cv_location="cv.pdf")
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.side_effect = [True, False, False]
        mock_path_instance.suffix.lower.return_value = '.pdf'
        mock_extract.return_value = "PDF Content"
        mock_file.side_effect = OSError("permission denied")
        assert loader.load_cv_content() is True

    def test_get_content_before_load(self):
        loader = CVLoader()
        assert loader.get_content() is None


class TestCVLoaderTextPath:
    @patch("commonlib.cv_loader.Path")
    @patch("builtins.open", new_callable=mock_open, read_data="cached content")
    def test_load_cv_txt_when_pdf_also_exists(self, mock_file, mock_path):
        loader = CVLoader(cv_location="cv.pdf")
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.side_effect = [True, True, True]
        mock_path_instance.suffix.lower.return_value = '.pdf'
        assert loader.load_cv_content() is True
        assert loader.get_content() == "cached content"
