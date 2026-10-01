import pytest
from unittest.mock import MagicMock, patch
from commonlib.company_normalizer import UNSPECIFIED_COMPANY
from commonlib.sql.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.TecnoempleoService import TecnoempleoService
from scrapper.test.log_capture import assert_console_text, assert_logged, structured_fields

class TestTecnoempleoService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def mock_persistence_manager(self):
        return MagicMock(spec=PersistenceManager)
    
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return TecnoempleoService(mock_mysql, mock_persistence_manager, False)
    
    def test_initialization(self, service):
        assert service.web_page == 'Tecnoempleo'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("http://tecnoempleo.com/job-title/rf-1234567890", "rf-1234567890"),
        ("http://tecnoempleo.com/another/rf-0987654321?param=value", "rf-0987654321?param=value"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id

    def test_process_job_unspecified_company(self, service, mock_mysql):
        """A job without company is inserted, and not linked as duplicated, while the company is unspecified"""
        mock_mysql.insert.return_value = 1
        with patch('scrapper.services.TecnoempleoService.htmlToMarkdown', return_value="Markdown"):
            result = service.process_job("Title", UNSPECIFIED_COMPANY, "Location", "http://url/rf-123", None, "<html>")
        assert result is True
        params = mock_mysql.insert.call_args[0][0]
        assert params[2] == UNSPECIFIED_COMPANY
        assert params[-1] is None
        mock_mysql.fetchAll.assert_not_called()

    @pytest.mark.parametrize("salary", ["30.000 € - 36.000 € Bruto/año", None])
    def test_process_job_inserts_the_scraped_salary(self, service, mock_mysql, salary):
        """The pay range read from the offer row reaches the salary column, so the AI never has to infer it"""
        mock_mysql.insert.return_value = 1
        with patch('scrapper.services.TecnoempleoService.htmlToMarkdown', return_value="Markdown"):
            service.process_job("Title", "Company", "Location", "http://url/rf-123", salary, "<html>")
        assert mock_mysql.insert.call_args[0][0][4] == salary

    def test_process_job_logs_scraped_fields(self, service, mock_mysql):
        with patch('scrapper.services.TecnoempleoService.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.TecnoempleoService.logger') as log:
            mock_mysql.insert.return_value = 1
            service.process_job("Title", "Company", "Location", "http://url/rf-123", "30.000 € - 36.000 € Bruto/año", "<html>")
        assert_logged(log, 'info', 'tecnoempleo.job.scraped', job_id='rf-123', title='Title', company='Company', location='Location', salary='30.000 € - 36.000 € Bruto/año', easy_apply=False)
        assert_console_text(log, 'info', 'tecnoempleo.job.scraped', 'rf-123, Title,', end='')

    def test_process_job_logs_inserted_and_duplicated(self, service, mock_mysql):
        with patch('scrapper.services.TecnoempleoService.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.TecnoempleoService.find_last_duplicated', return_value=11), \
             patch('scrapper.services.TecnoempleoService.logger') as log:
            mock_mysql.insert.return_value = 4
            service.process_job("Title", "Company", "Location", "http://url/rf-123", None, "<html>")
        events = {c.args[0]: structured_fields(c.kwargs) for c in log.info.call_args_list}
        assert events['tecnoempleo.job.inserted'] == {'job_id': 'rf-123', 'insert_id': 4}
        assert events['tecnoempleo.job.duplicated'] == {'job_id': 'rf-123', 'duplicated_id': 11}
        assert_console_text(log, 'info', 'tecnoempleo.job.inserted', 'INSERTED 4!', end='')
