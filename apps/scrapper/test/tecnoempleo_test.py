import pytest
from unittest.mock import MagicMock, patch, call
from scrapper import tecnoempleo
from scrapper.tecnoempleo import run, searchJobs, loadAndProcessRow, processRow, getJobId, login
from scrapper.seleniumUtil import SeleniumUtil
from scrapper.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

from itertools import cycle

@pytest.fixture
def mock_selenium():
    with patch('scrapper.tecnoempleo.selenium', spec=SeleniumUtil) as mock:
        mock.driverUtil = MagicMock()
        yield mock

@pytest.fixture
def mock_mysql():
    with patch('scrapper.tecnoempleo.mysql', spec=MysqlUtil) as mock:
        yield mock

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.tecnoempleo.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestTecnoempleoScrapper:

    @pytest.mark.parametrize("scenario", [
        {"desc": "valid_insert", "title": "Job Title", "valid": True},
        {"desc": "validation_fail", "title": "", "valid": False}
    ])
    def test_process_row(self, mock_selenium, mock_mysql, scenario):
        # Mock selenium returns for processRow
        mock_selenium.getText.side_effect = cycle([scenario["title"], "Company Name", "Location"]) if scenario["valid"] else cycle(["", "", ""])
        mock_selenium.getHtml.return_value = "<p>Description</p>"
        mock_selenium.getUrl.return_value = "http://job.url/rf-123"
        mock_selenium.getElms.return_value = [] # For job data
        
        with patch('scrapper.tecnoempleo.validate', return_value=scenario["valid"]), \
             patch('scrapper.tecnoempleo.htmlToMarkdown', return_value="Description"), \
             patch('scrapper.tecnoempleo.mergeDuplicatedJobs'), \
             patch('scrapper.tecnoempleo.getJobId', return_value="rf-123"):
            
            if scenario["valid"]:
                mock_mysql.insert.return_value = 1
                processRow()
                mock_mysql.insert.assert_called_once()
                # Check if the title is in the insert call arguments
                # The first argument to insert is a tuple: (jobId, title, company, location, url, md, easyApply, WEB_PAGE)
                assert scenario["title"] == mock_mysql.insert.call_args[0][0][1]
            else:
                with pytest.raises(ValueError, match='Validation failed'):
                    processRow()
                mock_mysql.insert.assert_not_called()

    def test_login(self, mock_selenium, mock_env_vars):
        
        with patch('scrapper.tecnoempleo.sleep'), \
             patch('scrapper.tecnoempleo.cloudFlareSecurityFilter') as mock_security, \
             patch('scrapper.tecnoempleo.USER_EMAIL', 'test@email.com'), \
             patch('scrapper.tecnoempleo.USER_PWD', 'password'):
             
             mock_selenium.driverUtil.useUndetected = False
             
             login()
             
             mock_selenium.waitAndClick.assert_called()
             mock_security.assert_called_once()
             mock_selenium.sendKeys.assert_any_call('#e_mail', 'test@email.com')
