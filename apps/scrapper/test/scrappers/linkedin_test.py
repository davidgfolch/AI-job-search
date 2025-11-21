import pytest
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import NoSuchElementException
from scrapper.scrappers.linkedin_scrapper import LinkedInScrapper

class TestLinkedInScrapper:
    @pytest.fixture
    def mockSelenium(self):
        selenium = MagicMock()
        selenium.getText.return_value = '100'
        selenium.getElms.return_value = []
        selenium.getAttr.return_value = 'https://linkedin.com/jobs/view/123/'
        selenium.getHtml.return_value = '<div>Job description</div>'
        return selenium
    
    @pytest.fixture
    @patch('scrapper.scrappers.linkedin_scrapper.getAndCheckEnvVars')
    def scrapper(self, mockGetEnv):
        mockGetEnv.return_value = ('test@email.com', 'password', 'python developer')
        return LinkedInScrapper()
    
    def test_initialization(self, scrapper):
        assert scrapper.userEmail == 'test@email.com'
        assert scrapper.userPwd == 'password'
        assert scrapper.jobsSearch == 'python developer'
        assert scrapper.webPage == 'LinkedIn'
        assert scrapper.jobsPerPage == 25
    
    def test_getSiteName(self, scrapper):
        assert scrapper.getSiteName() == 'LinkedIn'
    
    def test_login_success(self, scrapper, mockSelenium):
        result = scrapper.login(mockSelenium)
        assert result is True
        mockSelenium.loadPage.assert_called_once_with('https://www.linkedin.com/login')
        mockSelenium.sendKeys.assert_any_call('#username', 'test@email.com')
        mockSelenium.sendKeys.assert_any_call('#password', 'password')
        mockSelenium.waitAndClick.assert_called()
    
    def test_login_failure(self, scrapper, mockSelenium):
        mockSelenium.waitUntilPageUrlContains.side_effect = Exception('Login failed')
        result = scrapper.login(mockSelenium)
        assert result is False
    
    def test_buildSearchUrl(self, scrapper):
        url = scrapper._buildSearchUrl('python developer')
        assert 'linkedin.com/jobs/search' in url
        assert 'keywords=python' in url
        assert 'f_WT=2' in url
        assert 'geoId=105646813' in url
    
    def test_checkResults_no_results(self, scrapper, mockSelenium):
        mockSelenium.getElms.return_value = [MagicMock()]
        result = scrapper._checkResults(mockSelenium, 'python', 'http://test')
        assert result is False
    
    def test_checkResults_has_results(self, scrapper, mockSelenium):
        mockSelenium.getElms.return_value = []
        result = scrapper._checkResults(mockSelenium, 'python', 'http://test')
        assert result is True
    
    def test_getTotalResults(self, scrapper, mockSelenium):
        mockSelenium.getText.return_value = '150+ results'
        total = scrapper._getTotalResults(mockSelenium, 'python')
        assert total == 150
    
    def test_replaceIndex(self, scrapper):
        result = scrapper._replaceIndex('li:nth-child(##idx##)', 5)
        assert result == 'li:nth-child(5)'
    
    def test_getJobId(self, scrapper):
        url = 'https://www.linkedin.com/jobs/view/123456789/details'
        jobId = scrapper._getJobId(url)
        assert jobId == 123456789
    
    def test_getJobUrlShort(self, scrapper):
        url = 'https://www.linkedin.com/jobs/view/123456789/details?refId=abc'
        shortUrl = scrapper._getJobUrlShort(url)
        assert shortUrl == 'https://www.linkedin.com/jobs/view/123456789/'
    
    @patch('scrapper.scrappers.linkedin_scrapper.htmlToMarkdown')
    def test_extractJobInfo(self, mockHtmlToMarkdown, scrapper, mockSelenium):
        mockHtmlToMarkdown.return_value = '# Job Description'
        mockSelenium.getText.side_effect = ['Software Engineer', 'Tech Corp', 'Madrid']
        mockSelenium.getAttr.return_value = 'https://linkedin.com/jobs/view/123/'
        mockSelenium.getElms.return_value = [MagicMock()]
        jobData = scrapper._extractJobInfo(mockSelenium, 1, 'css-selector')
        assert jobData['job_id'] == 123
        assert jobData['title'] == 'Software Engineer'
        assert jobData['company'] == 'Tech Corp'
        assert jobData['location'] == 'Madrid'
        assert jobData['easy_apply'] is True
        assert jobData['web_page'] == 'LinkedIn'
    
    def test_clickNextPage_success(self, scrapper, mockSelenium):
        result = scrapper._clickNextPage(mockSelenium)
        assert result is True
        mockSelenium.waitAndClick.assert_called()
    
    def test_clickNextPage_failure(self, scrapper, mockSelenium):
        mockSelenium.waitAndClick.side_effect = NoSuchElementException('No next button')
        result = scrapper._clickNextPage(mockSelenium)
        assert result is False
    
    def test_scrollToJob_success(self, scrapper, mockSelenium):
        mockSelenium.getElm.return_value = MagicMock()
        cssSel = scrapper._scrollToJob(mockSelenium, 1)
        assert 'nth-child(1)' in cssSel
        mockSelenium.scrollIntoView.assert_called()
    
    def test_scrollToJob_retry(self, scrapper, mockSelenium):
        mockSelenium.scrollIntoView.side_effect = [NoSuchElementException(), None]
        mockSelenium.getElm.return_value = MagicMock()
        with patch.object(scrapper, '_scrollJobsListRetry'):
            cssSel = scrapper._scrollToJob(mockSelenium, 1)
            assert cssSel is not None
    
    @patch('scrapper.scrappers.linkedin_scrapper.validate')
    @patch('scrapper.scrappers.linkedin_scrapper.htmlToMarkdown')
    def test_processJobItem_success(self, mockHtmlToMarkdown, mockValidate, scrapper, mockSelenium):
        mockHtmlToMarkdown.return_value = '# Job'
        mockValidate.return_value = True
        mockSelenium.getText.side_effect = ['Engineer', 'Company', 'Location']
        mockSelenium.getElm.return_value = MagicMock()
        mockSelenium.getElms.return_value = []
        jobData = scrapper._processJobItem(mockSelenium, 1)
        assert jobData is not None
        assert jobData['title'] == 'Engineer'
    
    @patch('scrapper.scrappers.linkedin_scrapper.validate')
    def test_processJobItem_validation_failure(self, mockValidate, scrapper, mockSelenium):
        mockValidate.return_value = False
        mockSelenium.getText.side_effect = ['', '', '']
        mockSelenium.getElm.return_value = MagicMock()
        mockSelenium.getElms.return_value = []
        jobData = scrapper._processJobItem(mockSelenium, 1)
        assert jobData is None
    
    def test_processJobItem_exception(self, scrapper, mockSelenium):
        mockSelenium.scrollIntoView.side_effect = Exception('Error')
        jobData = scrapper._processJobItem(mockSelenium, 1)
        assert jobData is None
    
    @patch('scrapper.scrappers.linkedin_scrapper.htmlToMarkdown')
    def test_processPage(self, mockHtmlToMarkdown, scrapper, mockSelenium):
        mockHtmlToMarkdown.return_value = '# Job'
        mockSelenium.getText.side_effect = ['Eng1', 'Co1', 'Loc1', 'Eng2', 'Co2', 'Loc2']
        mockSelenium.getElm.return_value = MagicMock()
        mockSelenium.getElms.return_value = []
        with patch.object(scrapper, '_processJobItem', return_value={'job_id': '1'}):
            jobs = scrapper._processPage(mockSelenium, 1, 0, 2)
            assert len(jobs) == 2
    
    def test_processPage_stops_on_errors(self, scrapper, mockSelenium):
        with patch.object(scrapper, '_processJobItem', return_value=None):
            jobs = scrapper._processPage(mockSelenium, 1, 0, 25)
            assert len(jobs) == 0
    
    @patch('scrapper.scrappers.linkedin_scrapper.printPage')
    def test_searchJobs_no_results(self, mockPrintPage, scrapper, mockSelenium):
        mockSelenium.getElms.return_value = [MagicMock()]
        jobs = scrapper.searchJobs(mockSelenium, 'python')
        assert len(jobs) == 0
    
    @patch('scrapper.scrappers.linkedin_scrapper.printPage')
    @patch('scrapper.scrappers.linkedin_scrapper.htmlToMarkdown')
    def test_searchJobs_with_results(self, mockHtmlToMarkdown, mockPrintPage, scrapper, mockSelenium):
        mockHtmlToMarkdown.return_value = '# Job'
        mockSelenium.getElms.return_value = []
        mockSelenium.getText.side_effect = ['25', 'Eng', 'Co', 'Loc']
        mockSelenium.getElm.return_value = MagicMock()
        with patch.object(scrapper, '_clickNextPage', return_value=False):
            with patch.object(scrapper, '_processJobItem', return_value={'job_id': '1'}):
                jobs = scrapper.searchJobs(mockSelenium, 'python')
                assert isinstance(jobs, list)
    
    def test_searchJobs_exception(self, scrapper, mockSelenium):
        mockSelenium.loadPage.side_effect = Exception('Load error')
        jobs = scrapper.searchJobs(mockSelenium, 'python')
        assert len(jobs) == 0
