import pytest
from unittest.mock import MagicMock, patch
from scrapper.executor.LinkedinExecutor import LinkedinExecutor
from scrapper.navigator.linkedinNavigator import LinkedinNavigator
from scrapper.services.LinkedinService import LinkedinService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mocks():
    with patch('scrapper.executor.LinkedinExecutor.LinkedinNavigator') as nav_cls, \
         patch('scrapper.executor.LinkedinExecutor.LinkedinService') as svc_cls, \
         patch('commonlib.mysqlUtil.MysqlUtil'), \
         patch('scrapper.util.persistence_manager.PersistenceManager'), \
         patch('scrapper.services.selenium.seleniumService.SeleniumService'), \
         patch('scrapper.executor.LinkedinExecutor.getAndCheckEnvVars', return_value=('u', 'p', 'k')), \
         patch('scrapper.executor.LinkedinExecutor.sleep'), \
         patch('scrapper.navigator.linkedinNavigator.sleep'):
        
        nav = nav_cls.return_value
        svc = svc_cls.return_value
        # Setup common mock behaviors
        nav.get_job_data.return_value = ("T", "C", "L", "U", "H")
        svc.job_exists_in_db.return_value = (None, False)
        yield {'nav': nav, 'svc': svc, 'nav_cls': nav_cls, 'svc_cls': svc_cls}

@pytest.fixture
def mock_selenium():
    return MagicMock(spec=SeleniumService)

@pytest.fixture
def mock_mysql():
    return MagicMock(spec=MysqlUtil)

@pytest.fixture
def mock_pm():
    return MagicMock(spec=PersistenceManager)

class TestLinkedinExecutor:
    def test_run_modes(self, mocks, mock_selenium, mock_pm):
        # Preload
        executor = LinkedinExecutor(mock_selenium, mock_pm)
        executor.run(preload_page=True)
        mocks['nav'].login.assert_called_with('u', 'p')
        
        # Normal
        mocks['svc'].should_skip_keyword.return_value = (False, 1)
        # Mock _process_keyword to call _search_jobs_loop? Or test logic inside?
        # Original tested run -> process_keyword.
        # Here run calls _execute_scrapping which calls _process_keyword.
        with patch.object(LinkedinExecutor, '_process_keyword') as pk:
             executor.run(preload_page=False)
             pk.assert_called_with('k', 1)

    def test_process_keyword_scenarios(self, mocks, mock_selenium, mock_pm):
        executor = LinkedinExecutor(mock_selenium, mock_pm)
        mocks['nav'].check_login_popup.return_value = False
        
        with patch.object(LinkedinExecutor, '_load_page', return_value="url"), \
             patch.object(LinkedinExecutor, '_search_jobs_loop') as search:
            
            # Results exist
            mocks['nav'].check_results.return_value = True
            executor._process_keyword('k', 1)
            search.assert_called()
            
            # No results
            search.reset_mock()
            mocks['nav'].check_results.return_value = False
            executor._process_keyword('k', 1)
            search.assert_not_called()

    def test_load_page(self, mocks, mock_selenium, mock_pm):
        executor = LinkedinExecutor(mock_selenium, mock_pm)
        assert 'linkedin.com' in executor._load_page('python')
        mocks['nav'].load_page.assert_called()

    @pytest.mark.parametrize("start_page,total_res,calls", [(1, 4, 1), (3, 100, 1)])
    def test_search_jobs_flow(self, mocks, mock_selenium, mock_pm, start_page, total_res, calls):
        executor = LinkedinExecutor(mock_selenium, mock_pm)
        # We need to set service on executor because _search_jobs_loop uses self.service
        executor.service = mocks['svc']
        
        mocks['nav'].get_total_results.return_value = total_res
        mocks['nav'].fast_forward_page.return_value = start_page
        mocks['nav'].click_next_page.return_value = True
        
        with patch.object(executor, '_load_and_process_row', return_value=False):
             executor._search_jobs_loop('k', start_page)
             if start_page > 1:
                assert mocks['nav'].click_next_page.call_count >= calls
             if total_res > 25:
                # Page updates happen
                assert mocks['svc'].update_state.call_count >= 1

    @pytest.mark.parametrize("exists, expected_result", [
        ((1, True), True), ((None, False), False)
    ])
    def test_load_and_process_row(self, mocks, mock_selenium, mock_pm, exists, expected_result):
        executor = LinkedinExecutor(mock_selenium, mock_pm)
        executor.service = mocks['svc']
        mocks['nav'].scroll_jobs_list.return_value = "css"
        mocks['svc'].job_exists_in_db.return_value = exists
        
        with patch.object(executor, '_process_row') as pr:
            result = executor._load_and_process_row(1)
            assert result is expected_result
            if exists[1]: 
                pr.assert_not_called()
            else:
                pr.assert_called()

    @pytest.mark.parametrize("idx, easy_apply, is_direct", [
        (1, True, False), (None, False, True)
    ])
    def test_process_row(self, mocks, mock_selenium, mock_pm, idx, easy_apply, is_direct):
        executor = LinkedinExecutor(mock_selenium, mock_pm)
        executor.service = mocks['svc']
        mocks['nav'].check_easy_apply.return_value = easy_apply
        
        executor._process_row(idx)
        mocks['svc'].process_job.assert_called_with("T", "C", "L", "U", "H", is_direct, easy_apply)

    def test_process_specific_url(self, mocks):
        with patch.object(LinkedinExecutor, '_process_row') as pr:
            # We need to mock instantiation of LinkedinExecutor inside process_specific_url
            # Since process_specific_url instantiates cls(), we can mock __init__?
            # Or mock cls directly if we patch the class in the module where it's called?
            # But we are testing the method on the class.
            # We can mock SeleniumService and MysqlUtil used inside.
            # And mock getAndCheckEnvVars? No, logic:
            
            # with MysqlUtil() as mysql, SeleniumService() as seleniumUtil:
            #      pm = PersistenceManager()
            #      executor = cls(seleniumUtil, pm)
            
            # We rely on 'u', 'p' from patched getAndCheckEnvVars in fixture.
            
            LinkedinExecutor.process_specific_url("http://url")
            
            # navigator.load_page is called
            mocks['nav'].load_page.assert_called_with("http://url")
            pr.assert_called_with(None)
    
    def test_transform_to_search_url(self):
        url = "https://www.linkedin.com/jobs/view/4350893693/"
        expected = "https://www.linkedin.com/jobs/search/?currentJobId=4350893693"
        assert LinkedinExecutor._transform_to_search_url(url) == expected
        url2 = "https://www.linkedin.com/jobs/search/?currentJobId=123"
        assert LinkedinExecutor._transform_to_search_url(url2) == url2
