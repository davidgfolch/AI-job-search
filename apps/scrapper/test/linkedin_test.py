import pytest
from unittest.mock import MagicMock, patch
from scrapper import linkedin
from scrapper.linkedin import run, load_page, search_jobs, process_row, processUrl, load_and_process_row
from scrapper.services.job_services.linkedin_job_service import LinkedinJobService
from scrapper.selenium.linkedin_selenium import LinkedinNavigator
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mocks():
    with patch('scrapper.linkedin.LinkedinNavigator') as nav_cls, \
         patch('scrapper.linkedin.LinkedinJobService') as svc_cls, \
         patch('scrapper.linkedin.MysqlUtil'), \
         patch('scrapper.linkedin.PersistenceManager'), \
         patch('scrapper.linkedin.SeleniumService'), \
         patch('scrapper.linkedin.getAndCheckEnvVars', return_value=('u', 'p', 'k')):
        
        nav = nav_cls.return_value
        svc = svc_cls.return_value
        # Setup common mock behaviors
        nav.get_job_data_in_detail_page.return_value = ("T", "C", "L", "U", "H")
        nav.get_job_data_in_list.return_value = ("T", "C", "L", "U", "H")
        svc.job_exists_in_db.return_value = (None, False)
        yield {'nav': nav, 'svc': svc, 'nav_cls': nav_cls, 'svc_cls': svc_cls}

class TestLinkedinScrapper:
    def test_run_modes(self, mocks):
        # Preload
        with patch('scrapper.linkedin.USER_EMAIL', 'u'), \
             patch('scrapper.linkedin.USER_PWD', 'p'), \
             patch('scrapper.linkedin.JOBS_SEARCH', 'k'):
            run(MagicMock(), True, MagicMock())
            mocks['nav'].login.assert_called_with('u', 'p')
            
            # Normal
            mocks['svc'].should_skip_keyword.return_value = (False, 1)
            with patch('scrapper.linkedin.process_keyword') as pk:
                run(MagicMock(), False, MagicMock())
                pk.assert_called_with('k', 1)

    def test_process_keyword_scenarios(self, mocks):
        linkedin.navigator = mocks['nav']
        mocks['nav'].check_login_popup.return_value = False
        
        with patch('scrapper.linkedin.load_page', return_value="url"), \
             patch('scrapper.linkedin.search_jobs') as search:
            
            # Results exist
            mocks['nav'].check_results.return_value = True
            linkedin.process_keyword('k', 1)
            search.assert_called()
            
            # No results
            search.reset_mock()
            mocks['nav'].check_results.return_value = False
            linkedin.process_keyword('k', 1)
            search.assert_not_called()

    def test_load_page(self, mocks):
        linkedin.navigator = mocks['nav']
        assert 'linkedin.com' in load_page('python')
        mocks['nav'].load_page.assert_called()

    @pytest.mark.parametrize("start_page,total_res,calls", [(1, 4, 1), (3, 100, 2)])
    def test_search_jobs_flow(self, mocks, start_page, total_res, calls):
        linkedin.navigator = mocks['nav']
        linkedin.service = mocks['svc']
        linkedin.JOBS_X_PAGE = 25
        mocks['nav'].get_total_results.return_value = total_res
        mocks['nav'].click_next_page.return_value = True
        
        with patch('scrapper.linkedin.load_and_process_row', return_value=True):
             search_jobs('k', start_page)
             if start_page > 1:
                 assert mocks['nav'].click_next_page.call_count >= calls
             if total_res > 25:
                assert mocks['svc'].update_state.call_count >= 1

    @pytest.mark.parametrize("exists, new, expected_process", [
        ((1, True), False, False), ((None, False), True, True)
    ])
    def test_load_and_process_row(self, mocks, exists, new, expected_process):
        linkedin.navigator = mocks['nav']
        linkedin.service = mocks['svc']
        mocks['nav'].scroll_jobs_list.return_value = "css"
        mocks['svc'].job_exists_in_db.return_value = exists
        
        with patch('scrapper.linkedin.process_row') as pr:
            assert load_and_process_row(1) is True
            if expected_process: pr.assert_called()
            else: pr.assert_not_called()

    @pytest.mark.parametrize("idx, easy_apply, is_direct", [
        (1, True, False), (None, False, True)
    ])
    def test_process_row(self, mocks, idx, easy_apply, is_direct):
        linkedin.navigator = mocks['nav']
        linkedin.service = mocks['svc']
        mocks['nav'].check_easy_apply.return_value = easy_apply
        
        process_row(idx)
        mocks['svc'].process_job.assert_called_with("T", "C", "L", "U", "H", is_direct, easy_apply)

    def test_processUrl(self, mocks):
        with patch('scrapper.linkedin.process_row') as pr:
            processUrl("http://url")
            mocks['nav'].load_page.assert_called_with("http://url")
            pr.assert_called_with(None)

class TestLinkedinJobService:
    @pytest.fixture
    def service(self):
        return LinkedinJobService(MagicMock(), MagicMock())
    
    def test_url_parsing(self, service):
        url = "https://www.linkedin.com/jobs/view/123456/?x=y"
        assert service.get_job_id(url) == 123456
        assert service.get_job_url_short(url) == "https://www.linkedin.com/jobs/view/123456/"

    def test_process_job(self, service):
        with patch('scrapper.services.job_services.linkedin_job_service.validate', side_effect=[True, False]), \
             patch('scrapper.services.job_services.linkedin_job_service.htmlToMarkdown', return_value="M"), \
             patch('scrapper.services.job_services.linkedin_job_service.mergeDuplicatedJobs'):
             
             # Valid
             service.mysql.jobExists.return_value = False
             service.process_job("T", "C", "L", "https://www.linkedin.com/jobs/view/123/", "H", False, False)
             service.mysql.insert.assert_called()
             
             # Invalid
             with pytest.raises(ValueError):
                 service.process_job("T", "C", "L", "U", "H", False, False)

    def test_persistence_methods(self, service):
        service.prepare_resume()
        service.persistence_manager.prepare_resume.assert_called_with('Linkedin')
        
        service.should_skip_keyword('k')
        service.persistence_manager.should_skip_keyword.assert_called_with('k')
        
        service.update_state('k', 1)
        service.persistence_manager.update_state.assert_called_with('Linkedin', 'k', 1)
        
        service.clear_state()
        service.persistence_manager.clear_state.assert_called_with('Linkedin')

    def test_job_exists_in_db(self, service):
        service.mysql.fetchOne.return_value = {"id": 123}
        id, exists = service.job_exists_in_db("https://www.linkedin.com/jobs/view/123/")
        assert id == 123
        assert exists is True
        
        service.mysql.fetchOne.return_value = None
        id, exists = service.job_exists_in_db("https://www.linkedin.com/jobs/view/456/")
        assert id == 456
        assert exists is False
        
    def test_set_debug(self, service):
        service.set_debug(True)
        assert service.debug is True

    def test_print_job(self, service):
        # Trigger print_job via process_job when job exists + direct url
        with patch('scrapper.services.job_services.linkedin_job_service.validate', return_value=True), \
             patch('scrapper.services.job_services.linkedin_job_service.htmlToMarkdown', return_value="M"):
            service.mysql.jobExists.return_value = True
            
            # Should call print_job (we can't easily mock print_job here since it's a method on the object under test, 
            # but we can verify it runs without error and covers the lines)
            service.process_job("T", "C", "L", "https://www.linkedin.com/jobs/view/123/", "H", True, False)
            service.mysql.insert.assert_not_called()

class TestLinkedinNavigator:
    def test_get_total_results(self):
        nav = LinkedinNavigator(MagicMock())
        nav.selenium.getText.return_value = "100+ items"
        assert nav.get_total_results("k", "r", "l", "t") == 100
