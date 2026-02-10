import pytest
from unittest.mock import MagicMock, patch
from scrapper.services.InfojobsService import InfojobsService, REMOVE_IN_MARKDOWN
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager

class TestInfojobsService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def mock_persistence_manager(self):
        return MagicMock(spec=PersistenceManager)
    
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return InfojobsService(mock_mysql, mock_persistence_manager, False)
    
    def test_initialization(self, service):
        assert service.web_page == 'Infojobs'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.infojobs.net/of-1234567890?other=param", "1234567890"),
        ("https://www.infojobs.net/of-0987654321", "0987654321"),
        ("https://www.infojobs.net/of-123", "123"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id
    
    def test_job_exists_in_db(self, service, mock_mysql):
        mock_mysql.fetchOne.return_value = {"id": 1}
        job_id, exists = service.job_exists_in_db("https://www.infojobs.net/of-123")
        assert job_id == "123"
        assert exists is True
        mock_mysql.fetchOne.return_value = None
        job_id, exists = service.job_exists_in_db("https://www.infojobs.net/of-456")
        assert job_id == "456"
        assert exists is False
    
    def test_process_job_valid(self, service, mock_mysql):
        with patch('scrapper.services.InfojobsService.htmlToMarkdown', return_value="Markdown"), \
             patch('scrapper.services.InfojobsService.validate', return_value=True), \
             patch('scrapper.services.InfojobsService.find_last_duplicated'):
            mock_mysql.insert.return_value = 1
            result = service.process_job("Title", "Company", "Location", "https://www.infojobs.net/of-123", "<html>")
            assert result is True
            mock_mysql.insert.assert_called_once()
    
    @pytest.mark.parametrize("input_md, required_substrings", [
        ("# Job Title\n\nDescription of the job.\n\n\n¿Te gusta esta oferta?\nPrueba el Asistente de IA y mejora tus posibilidades.\n\nAsistente IA\n\n\nRequirements...", ["Description of the job.", "Requirements..."]),
        ("# Job Title\nContent\n\n¿Te gusta esta oferta?   \n  \nPrueba el Asistente de IA y mejora tus posibilidades.\n  \nAsistente IA\n\nMore Content", ["Content", "More Content"])
    ])
    def test_post_process_markdown(self, service, input_md, required_substrings):
        cleaned_md = service.post_process_markdown(input_md)
        for remove in REMOVE_IN_MARKDOWN:
            assert remove not in cleaned_md
        for required in required_substrings:
            assert required in cleaned_md
