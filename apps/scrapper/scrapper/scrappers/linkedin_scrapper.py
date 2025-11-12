import math
import re
import traceback
from typing import List, Dict, Any
from urllib.parse import quote
from selenium.common.exceptions import NoSuchElementException
from ..interfaces.scrapper_interface import ScrapperInterface
from ..seleniumUtil import SeleniumUtil
from ..baseScrapper import getAndCheckEnvVars, htmlToMarkdown, join, printPage, validate, debug as baseDebug
from ..selectors.linkedinSelectors import *
from commonlib.terminalColor import green, red, yellow
from commonlib.decorator.retry import retry

DEBUG = False

class LinkedInScrapper(ScrapperInterface):
    def __init__(self):
        self.userEmail, self.userPwd, self.jobsSearch = getAndCheckEnvVars("LINKEDIN")
        self.remote = '2'
        self.location = '105646813'
        self.fTpr = 'r86400'
        self.jobsPerPage = 25
        self.webPage = 'LinkedIn'

    def getSiteName(self) -> str:
        return self.webPage
    
    def login(self, selenium: SeleniumUtil) -> bool:
        print(yellow('Logging into LinkedIn...'))
        try:
            selenium.loadPage('https://www.linkedin.com/login')
            selenium.sendKeys('#username', self.userEmail)
            selenium.sendKeys('#password', self.userPwd)
            try:
                selenium.checkboxUnselect('div.remember_me__opt_in input')
            except Exception:
                pass
            selenium.waitAndClick('form button[type=submit]')
            print(yellow('Waiting for LinkedIn to redirect to feed page...',
                         '(Maybe you need to solve a security filter first)'))
            selenium.waitUntilPageUrlContains('https://www.linkedin.com/feed/', 60)
            print(green('Login successful!'))
            return True
        except Exception:
            baseDebug(DEBUG, 'Login failed', exception=True)
            return False
    
    def searchJobs(self, selenium: SeleniumUtil, keywords: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            print(yellow(f'Search keyword={keywords}'))
            url = self._buildSearchUrl(keywords)
            print(yellow(f'Loading page {url}'))
            selenium.loadPage(url)
            selenium.waitUntilPageIsLoaded()
            if not self._checkResults(selenium, keywords, url):
                return jobs
            self._hideUiElements(selenium)
            totalResults = self._getTotalResults(selenium, keywords)
            totalPages = math.ceil(totalResults / self.jobsPerPage)
            page = 1
            currentItem = 0
            while True:
                printPage(self.webPage, page, totalPages, keywords)
                pageJobs = self._processPage(selenium, page, currentItem, totalResults)
                jobs.extend(pageJobs)
                currentItem += len(pageJobs)
                if currentItem >= totalResults or page >= totalPages or not self._clickNextPage(selenium):
                    break
                page += 1
                selenium.waitUntilPageIsLoaded()
            self._printSummary(keywords, totalResults, currentItem)
        except Exception:
            baseDebug(DEBUG, 'Error searching jobs', exception=True)
        return jobs
    
    def extractJobData(self, selenium: SeleniumUtil, jobElement) -> Dict[str, Any]:
        return self._extractJobInfo(selenium, jobElement, '')
    
    def _buildSearchUrl(self, keywords: str) -> str:
        return join('https://www.linkedin.com/jobs/search/?',
                   '&'.join([
                       f'keywords={quote(keywords)}',
                       f'f_WT={self.remote}',
                       f'geoId={self.location}',
                       f'f_TPR={self.fTpr}'
                   ]))
    
    def _checkResults(self, selenium: SeleniumUtil, keywords: str, url: str) -> bool:
        noResultElms = selenium.getElms(CSS_SEL_NO_RESULTS)
        if len(noResultElms) > 0:
            print(red(f'No results for keywords={keywords} URL={url}'))
            return False
        return True
    
    def _hideUiElements(self, selenium: SeleniumUtil):
        selenium.waitAndClick_noError(CSS_SEL_MESSAGES_HIDE, 'Could not collapse messages')

    def _getTotalResults(self, selenium: SeleniumUtil, keywords: str) -> int:
        from commonlib.terminalColor import printHR
        totalText = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
        total = int(totalText.replace('+', ''))
        printHR(green)
        print(green(f'{total} total results for search: {keywords} (remote={self.remote}, location={self.location}, last={self.fTpr})'))
        printHR(green)
        return total
    
    def _processPage(self, selenium: SeleniumUtil, page: int, currentItem: int, totalResults: int) -> List[Dict[str, Any]]:
        jobs = []
        errors = 0
        for idx in range(1, self.jobsPerPage + 1):
            if currentItem + idx > totalResults:
                break
            print(green(f'pg {page} job {idx} - '), end='', flush=True)
            jobData = self._processJobItem(selenium, idx)
            if jobData:
                jobs.append(jobData)
            else:
                errors += 1
                if errors > 1:
                    break
        return jobs
    
    def _processJobItem(self, selenium: SeleniumUtil, idx: int) -> Dict[str, Any]:
        try:
            cssSel = self._scrollToJob(selenium, idx)
            jobData = self._extractJobInfo(selenium, idx, cssSel)
            if jobData and validate(jobData['title'], jobData['url'], 
                                   jobData['company'], jobData['markdown'], False):
                return jobData
        except Exception:
            baseDebug(DEBUG, f'Error processing job {idx}', exception=True)
        finally:
            print(flush=True)
        return None
    
    def _scrollToJob(self, selenium: SeleniumUtil, idx: int) -> str:
        cssSel = self._replaceIndex(CSS_SEL_JOB_LINK, idx)
        try:
            selenium.scrollIntoView(cssSel)
        except NoSuchElementException:
            self._scrollJobsListRetry(selenium, idx)
            selenium.scrollIntoView(cssSel)
        selenium.moveToElement(selenium.getElm(cssSel))
        selenium.waitUntilClickable(cssSel)
        return cssSel
    
    def _extractJobInfo(self, selenium: SeleniumUtil, idx: int, cssSel: str) -> Dict[str, Any]:
        liPrefix = self._replaceIndex(CSS_SEL_JOB_LI_IDX, idx)
        title = selenium.getText(f'{liPrefix} {LI_JOB_TITLE_CSS_SUFFIX}')
        company = selenium.getText(f'{liPrefix} {CSS_SEL_COMPANY}')
        location = selenium.getText(f'{liPrefix} {CSS_SEL_LOCATION}')
        selenium.waitUntilClickable(CSS_SEL_JOB_HEADER)
        url = self._getJobUrlShort(selenium.getAttr(CSS_SEL_JOB_HEADER, 'href'))
        jobId = self._getJobId(url)
        if idx != 1:
            print(yellow('loading...'), end='', flush=True)
            selenium.waitAndClick(cssSel)
        html = selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        markdown = htmlToMarkdown(html)
        easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
        print(f'{jobId}, {title}, {company}, {location}, easy_apply={easyApply} - ', end='', flush=True)
        return {
            'job_id': jobId,
            'title': title,
            'company': company,
            'location': location,
            'url': url,
            'markdown': markdown,
            'easy_apply': easyApply,
            'web_page': self.webPage
        }
    
    @retry(exception=NoSuchElementException, raiseException=False)
    def _clickNextPage(self, selenium: SeleniumUtil) -> bool:
        selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
        return True
    
    @retry()
    def _scrollJobsListRetry(self, selenium: SeleniumUtil, idx: int):
        cssSelI = self._replaceIndex(CSS_SEL_JOB_LI_IDX, idx)
        selenium.scrollIntoView(cssSelI)
        selenium.moveToElement(selenium.getElm(cssSelI))
        selenium.waitUntilClickable(self._replaceIndex(CSS_SEL_JOB_LINK, idx))

    def _replaceIndex(self, cssSelector: str, idx: int) -> str:
        return cssSelector.replace('##idx##', str(idx))
    
    def _getJobId(self, url: str) -> int:
        return int(re.sub(r'.*/jobs/view/([^/]+)/.*', r'\1', url))
    
    def _getJobUrlShort(self, url: str) -> str:
        return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)
    
    def _printSummary(self, keywords: str, totalResults: int, currentItem: int):
        from commonlib.terminalColor import printHR
        from commonlib.util import getDatetimeNowStr
        printHR()
        print(f'{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords} (remote={self.remote} location={self.location} last={self.fTpr})')
        printHR()
        print()

def debug(msg: str = ''):
    baseDebug(DEBUG, msg)