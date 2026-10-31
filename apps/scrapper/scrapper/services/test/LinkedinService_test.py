import pytest
from unittest.mock import MagicMock, patch
from commonlib.sql.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.LinkedinService import LinkedinService
from scrapper.test.log_capture import assert_console_text, assert_logged, structured_fields

FIT_CARD_MD = (
    'Hybrid, Full-time\n\nYour profile and resume match the required qualifications well\n\nBETA • Is this information helpful?\n\n'
    '[Reactivate Premium](https://www.linkedin.com/premium/products/?upsellOrderOrigin=x)\n\nAbout the job\n-------------\n\n'
    '**About JetBrains**  We create intelligent software development tools.\n\n---\n\nBenefits found in job post\n\nMedical insurance\n\n'
    'Job search faster with Premium\n\nAbout the company\n\nTrending employee content\n\n[Show more](https://www.linkedin.com/company/jetbrains/life/)\n'
)

TRENDS_CARD_MD = (
    'On-site, Full-time\n\nSee recent hiring trends for Advanced Field Solutions Ltd\n\n'
    'Access exclusive applicant insights, see jobs where you have the highest chance of hearing back, and more.\n\n'
    '[Reactivate Premium](https://www.linkedin.com/premium/products/?x)\n\nAbout the job\n-------------\n\n'
    'About AFS\n\nAdvanced Field Solutions Ltd (AFS) builds field-service management products.\n'
)

CLEAN_MD = (
    '70K EUR/yr - 120K EUR/yr + Bonus, Stock options, Hybrid, Full-time\n\nAbout the job\n-------------\n\n'
    '💻 **Job Title:**  AI Engineer\n\n---\n\nRequirements added by the job poster\n\n'
    '• 4+ years of work experience with Python (Programming Language)\n'
)

# A clean offer whose description legitimately mentions the company section: the guard must leave it alone
COMPANY_IN_DESCRIPTION_MD = 'Remote, Full-time\n\nAbout the job\n-------------\n\nAbout the company\n\nWe build agents for enterprises.\n'

class TestLinkedinService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def mock_persistence_manager(self):
        return MagicMock(spec=PersistenceManager)
    
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return LinkedinService(mock_mysql, mock_persistence_manager, False)
    
    def test_initialization(self, service):
        assert service.web_page == 'Linkedin'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.linkedin.com/jobs/view/12345/", 12345),
        ("https://www.linkedin.com/jobs/view/67890/other-params", 67890),
        ("https://www.linkedin.com/jobs/view/111/", 111),
        ("https://www.linkedin.com/jobs/view/123456/?x=y", 123456),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id
    
    @pytest.mark.parametrize("url, expected_short", [
        ("https://www.linkedin.com/jobs/view/12345/other-params", "https://www.linkedin.com/jobs/view/12345/"),
        ("https://www.linkedin.com/jobs/view/67890/", "https://www.linkedin.com/jobs/view/67890/"),
        ("https://www.linkedin.com/jobs/view/123456/?x=y", "https://www.linkedin.com/jobs/view/123456/"),
    ])
    def test_get_job_url_short(self, service, url, expected_short):
        assert service.get_job_url_short(url) == expected_short
    
    @pytest.mark.parametrize("fetch_result, expected_exists", [
        ({"id": 1}, True),
        (None, False),
    ])
    def test_job_exists_in_db(self, service, mock_mysql, fetch_result, expected_exists):
        mock_mysql.fetchOne.return_value = fetch_result
        url = "https://www.linkedin.com/jobs/view/12345/"
        job_id, exists = service.job_exists_in_db(url)
        assert job_id == 12345
        assert exists is expected_exists
    
    def test_process_job_valid(self, service, mock_mysql):
        with patch('scrapper.core.baseScrapper.validate', return_value=True), \
             patch('scrapper.core.baseScrapper.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.LinkedinService.find_last_duplicated'):
            mock_mysql.jobExists.return_value = False
            mock_mysql.insert.return_value = 1
            service.process_job("Title", "Company", "Loc", "https://www.linkedin.com/jobs/view/123/", "HTML", False, False)
            mock_mysql.insert.assert_called()
    
    def test_process_job_invalid(self, service):
        with patch('scrapper.core.baseScrapper.validate', return_value=False):
            with pytest.raises(ValueError):
                service.process_job("T", "C", "L", "U", "H", False, False)
    
    def test_process_job_existing_direct_url(self, service, mock_mysql):
        with patch('scrapper.core.baseScrapper.validate', return_value=True), \
             patch('scrapper.core.baseScrapper.htmlToMarkdown', return_value="MD"):
            mock_mysql.jobExists.return_value = True
            service.process_job("Title", "Company", "Loc", "https://www.linkedin.com/jobs/view/123/", "HTML", True, False)
            mock_mysql.insert.assert_not_called()
    
    def test_prepare_resume(self, service, mock_persistence_manager):
        service.prepare_resume()
        mock_persistence_manager.prepare_resume.assert_called_with('Linkedin')
    
    def test_should_skip_keyword(self, service, mock_persistence_manager):
        mock_persistence_manager.should_skip_keyword.return_value = (True, 1)
        assert service.should_skip_keyword('python') == (True, 1)
        mock_persistence_manager.should_skip_keyword.assert_called_with('python')
    
    def test_update_state(self, service, mock_persistence_manager):
        service.update_state('python', 5)
        mock_persistence_manager.update_state.assert_called_with('Linkedin', 'python', 5)
    
    def test_clear_state(self, service, mock_persistence_manager):
        service.clear_state()
        mock_persistence_manager.clear_state.assert_called_with('Linkedin')

    def test_print_job_logs_lengths_not_blobs(self, service):
        with patch('scrapper.services.LinkedinService.logger') as log:
            service.print_job('T', 'C', 'L', 'U', 123, '<h1>x</h1>', 'MD')
        assert_logged(log, 'debug', 'linkedin.job.already_exists', job_id=123, title='T', company='C', location='L', url='U', html_length=10, markdown_length=2)
        assert_console_text(log, 'debug', 'linkedin.job.already_exists', 'TITLE=T')

    def test_update_job_logs_event(self, service, mock_mysql):
        with patch('scrapper.services.LinkedinService.logger') as log:
            service.update_job(123, 'T', 'C', 'L', 'U', 'H', 'MD', False)
        assert_logged(log, 'info', 'linkedin.job.updated', job_id=123)
        assert_console_text(log, 'info', 'linkedin.job.updated', 'Job updated 123')
        mock_mysql.executeAndCommit.assert_called_once()

    def test_process_job_logs_inserted_and_duplicated(self, service, mock_mysql):
        with patch('scrapper.core.baseScrapper.validate', return_value=True), \
             patch('scrapper.core.baseScrapper.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.LinkedinService.find_last_duplicated', return_value=77), \
             patch('scrapper.services.LinkedinService.logger') as log:
            mock_mysql.jobExists.return_value = False
            mock_mysql.insert.return_value = 5
            service.process_job("T", "C", "L", "https://www.linkedin.com/jobs/view/9/", "H", False, False)
        events = {c.args[0]: structured_fields(c.kwargs) for c in log.debug.call_args_list + log.info.call_args_list}
        assert events['linkedin.job.inserted'] == {'job_id': 9, 'insert_id': 5}
        assert events['linkedin.job.duplicated'] == {'job_id': 9, 'duplicated_id': 77}
        assert_console_text(log, 'info', 'linkedin.job.inserted', 'INSERTED 5!', end='')

    def test_process_job_logs_scraped_fields(self, service, mock_mysql):
        with patch('scrapper.core.baseScrapper.validate', return_value=True), \
             patch('scrapper.core.baseScrapper.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.LinkedinService.find_last_duplicated', return_value=None), \
             patch('scrapper.services.LinkedinService.logger') as log:
            mock_mysql.jobExists.return_value = False
            mock_mysql.insert.return_value = 1
            service.process_job("T", "C", "L", "https://www.linkedin.com/jobs/view/9/", "H", False, True)
        assert_logged(log, 'info', 'linkedin.job.scraped', job_id=9, title='T', company='C', location='L', easy_apply=True)
        assert_console_text(log, 'info', 'linkedin.job.scraped', '9, T,', end='')

    @pytest.mark.parametrize("input_md, required, forbidden", [
        (FIT_CARD_MD, ['Hybrid, Full-time', 'About the job\n-------------', 'Benefits found in job post', 'Medical insurance'],
         ['Your profile and resume', 'Reactivate Premium', 'Job search faster with Premium', 'Trending employee content', 'Show more']),
        (TRENDS_CARD_MD, ['On-site, Full-time', 'About the job', 'Advanced Field Solutions Ltd'],
         ['See recent hiring trends', 'Reactivate Premium']),
        (CLEAN_MD, ['About the job', 'Requirements added by the job poster'], []),
        (COMPANY_IN_DESCRIPTION_MD, ['About the company', 'We build agents'], []),
        ('MD', ['MD'], []),
        ('No heading\n\nJob search faster with Premium\n\nAbout the company', ['No heading'], ['Job search faster with Premium']),
    ])
    def test_post_process_markdown(self, service, input_md, required, forbidden):
        cleaned = service.post_process_markdown(input_md)
        for text in required:
            assert text in cleaned
        for text in forbidden:
            assert text not in cleaned

    @pytest.mark.parametrize("md", [CLEAN_MD, COMPANY_IN_DESCRIPTION_MD, 'MD'])
    def test_post_process_markdown_keeps_clean_markdown(self, service, md):
        assert service.post_process_markdown(md) == md

    @pytest.mark.parametrize("md, expected", [
        ('Description text.… more', 'Description text.'),
        ('Description text.…more', 'Description text.'),
        ('Description text.... more', 'Description text.'),
        ('Description text.\n\n… more', 'Description text.'),
        ('Description text.… less', 'Description text.'),
        ('A legit sentence ends with more.', 'A legit sentence ends with more.'),
        ('Description text.', 'Description text.'),
    ])
    def test_strip_expander_label(self, service, md, expected):
        assert service._strip_expander_label(md) == expected

    @pytest.mark.parametrize("md", ['Description text.… more', 'Description text.… less'])
    def test_strip_expander_label_warns(self, service, md):
        with patch('scrapper.services.LinkedinService.logger') as log:
            service._strip_expander_label(md)
        assert_logged(log, 'warning', 'linkedin.description.expander_label_stripped', markdown_length=len(md))
