import math
import time
import re
import traceback
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import (
    getAndCheckEnvVars, htmlToMarkdown, join, printPage, printScrapperTitle, removeLinks,
    validate)
from ai_job_search.tools.terminalColor import green, printHR, red, yellow
from ai_job_search.tools.decorator.retry import StackTrace, retry
from ai_job_search.tools.util import getDatetimeNowStr
from ai_job_search.viewer.clean.mergeDuplicates import (
    getSelect, mergeDuplicatedJobs)
from .seleniumUtil import SeleniumUtil, sleep
from ai_job_search.tools.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from .selectors.infojobsSelectors import (
    CSS_SEL_JOB_DETAIL,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND,
    CSS_SEL_COMPANY,
    CSS_SEL_LOCATION,
    CSS_SEL_JOB_TITLE,
    CSS_SEL_JOB_LI,
    CSS_SEL_JOB_LINK,
    CSS_SEL_NEXT_PAGE_BUTTON,
    CSS_SEL_SECURITY_FILTER1,
    CSS_SEL_SECURITY_FILTER2)


USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("INFOJOBS")

# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False

WEB_PAGE = 'Infojobs'
LIST_URL = 'https://www.infojobs.net/ofertas-trabajo'
JOBS_X_PAGE = 22  # NOT ALWAYS, SOMETIMES LESS REGARDLESS totalResults

LOGIN_WAIT_DISABLE = False

print('Infojobs scrapper init')
selenium: SeleniumUtil = None
mysql: MysqlUtil = None


def run(seleniumUtil: SeleniumUtil, preloadPage: bool):
    """Process jobs in search paginated list results"""
    global selenium, mysql
    selenium = seleniumUtil
    printScrapperTitle('Infojobs', preloadPage)
    if preloadPage:
        searchJobs(JOBS_SEARCH.split(',')[0], True)
        return
    with MysqlUtil() as mysql:
        for keywords in JOBS_SEARCH.split(','):
            searchJobs(keywords.strip(), False)


@retry(retries=10, delay=5, exception=NoSuchElementException)
def acceptCookies():
    print(yellow('SOLVE A SECURITY FILTER in selenium webbrowser...'), end='')
    sleep(4, 4)
    selenium.scrollIntoView('#didomi-notice-agree-button > span')
    sleep(2, 6)
    selenium.waitAndClick('#didomi-notice-agree-button > span')
    sleep(2, 6)


def securityFilter():
    selenium.waitUntilPageIsLoaded()
    sleep(4, 4)
    selenium.waitAndClick(CSS_SEL_SECURITY_FILTER1)
    selenium.waitAndClick(CSS_SEL_SECURITY_FILTER2)
    try:
        acceptCookies()
    except NoSuchElementException:
        print(yellow('Could not accept cookies'))
    selenium.waitUntilPageUrlContains('https://www.infojobs.net', 60)


def replaceIndex(cssSelector: str, idx: int):
    return cssSelector.replace('##idx##', str(idx))


def getTotalResultsFromHeader(keywords: str) -> int:
    total = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
    printHR()
    print(green(join(f'{total} total results for search: {keywords}')))
    printHR()
    return int(total)


def summarize(keywords, totalResults, currentItem):
    printHR()
    print(f'{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords}')
    printHR()
    print()


def scrollToBottom():
    """ pre scroll to bottom to force load of li's """
    print("scrollToBottom... ", end='')
    # this this can contain "pagination" or "Nueva busqueda"
    # when no pagination exists
    # selenium.scrollIntoView('div.ij-SearchListingPageContent-main main>div')
    selenium.scrollToBottom()
    sleep(3, 3)

@retry(exception=NoSuchElementException, raiseException=False)
def clickNextPage():
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
    return True


def loadJobDetail(jobLinkElm: WebElement):
    # first job in page loads automatically
    # if job exists in DB no need to load details (rate limit)
    print(yellow('loading...'), end='')
    jobLinkElm.click()


def jobExistsInDB(url):
    jobId = getJobId(url)
    return (jobId, mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, jobId) is not None)


def getJobId(url: str):
    return re.sub(r'.+/of-([^?/]+).*', r'\1', url)


def getJobUrlShort(url: str):
    return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)


def searchJobs(keywords: str, preloadPage: bool):
    try:
        print(yellow(f'Search keyword={keywords}'))
        loadSearchPage()
        if preloadPage:
            securityFilter()
            return
        if not loadFilteredSearchResults(keywords):
            return
        totalResults = getTotalResultsFromHeader(keywords)
        totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        page = 1
        currentItem = 0
        while currentItem < totalResults:
            printPage(WEB_PAGE, page, totalPages, keywords)
            idx = 0
            while idx < JOBS_X_PAGE and currentItem < totalResults:
                #Note JOBS_X_PAGE is not always exact
                print(green(f'pg {page} job {idx+1} - '), end='', flush=True)
                if loadAndProcessRow(idx):
                    currentItem += 1
                print()
                idx += 1
            if currentItem < totalResults:
                if clickNextPage():
                    page += 1
                    selenium.waitUntilPageIsLoaded()
                    time.sleep(5)
                else:
                    break  # exit while
        summarize(keywords, totalResults, currentItem)
    except Exception:
        debug(exception=True)


def loadSearchPage():
    if selenium.getUrl().find('infojobs.net') == -1:
        print(yellow(f'Loading search-jobs page'))
        selenium.loadPage('https://www.infojobs.net/')
    else:
        print(yellow(f'Click on search-jobs button'))
        clickOnSearchJobs()


def loadFilteredSearchResults(keywords: str):
    clickOnSearchJobs()
    selenium.sendKeys('.ij-SidebarFilter #fieldsetKeyword',keywords, clear=True)
    selenium.waitAndClick('.ij-SidebarFilter #buttonKeyword', scrollIntoView=True)
    sleep(1, 2)
    selenium.sendEscapeKey()
    selenium.waitAndClick('.ij-SidebarFilter input[type="radio"][value="_7_DAYS"]', scrollIntoView=True)
    sleep(1, 2)
    if selenium.getElms('.ij-OfferList-NoResults-title').__len__() > 0:
        print(yellow('No results for this search'))
        return False
    selenium.waitAndClick('.ij-SidebarFilter #check-teleworking--2', scrollIntoView=True)
    sleep(1, 2)
    return True


@retry(exceptionFnc=securityFilter)
def clickOnSearchJobs():
    selenium.waitAndClick('header nav ul li a[href="/ofertas-trabajo"]', scrollIntoView=True)
    selenium.waitUntilPageIsLoaded()    


@retry()
def scrollJobsList(idx):
    links = selenium.getElms(CSS_SEL_JOB_LINK)
    if idx >= len(links): # if link not found, scroll all list to properly load dynamic links' class in DOM
        for li in selenium.getElms(CSS_SEL_JOB_LI)[len(links)-1:]:
            selenium.scrollIntoView(li)
    selenium.scrollIntoView(selenium.getElms(CSS_SEL_JOB_LINK)[idx])


def loadAndProcessRow(idx) -> bool:
    try:
        if idx > 2:
            try:
                scrollJobsList(idx)
            except Exception as e:
                print(yellow(f'Could not scroll to link {idx}, IGNORING.'), end='')
                return False
        jobLinkElm: WebElement = selenium.getElms(CSS_SEL_JOB_LINK)[idx]
        url = jobLinkElm.get_attribute('href')
        jobId, jobExists = jobExistsInDB(url)
        if jobExists:
            print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'), end='')
            return True
        loadJobDetail(jobLinkElm)
        if not processRow(url):
            raise ValueError('Validation failed')
    except Exception as ex:
        print(red(f'ERROR: {ex}'))
        debug(red(traceback.format_exc()))
        return False
    finally:
        if LIST_URL not in selenium.getUrl():
            selenium.back()
    return True


@retry()
def processRow(url):
    sleep(5, 6)
    # try:
    title = selenium.getText(CSS_SEL_JOB_TITLE)
    company = selenium.getText(CSS_SEL_COMPANY)
    location = selenium.getText(CSS_SEL_LOCATION)
    jobId = getJobId(url)
    html = selenium.getHtml(CSS_SEL_JOB_DETAIL)
    md = htmlToMarkdown(html)
    md = postProcessMarkdown(md)
    # easyApply: there are 2 buttons
    # easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
    print(f'{jobId}, {title}, {company}, {location}  - ', end='')
    if validate(title, url, company, md, DEBUG):
        if id := mysql.insert((jobId, title, company, location, url, md,
                               None, WEB_PAGE)):
            print(green(f'INSERTED {id}!'), end='')
            mergeDuplicatedJobs(mysql, getSelect())
            return True
    return False


def postProcessMarkdown(md):
    txt = removeLinks(md)
    # txt = re.sub(r'\[([^\]]+)\]\(/ofertas-trabajo[^\)]+\)', r'\1', md)
    # txt = re.sub(r'[\\]+-', '-', txt)
    # txt = re.sub(r'[\\]+\.', '.', txt)
    # txt = re.sub(r'-\n', '\n', txt)
    # txt = re.sub(r'(\n[  ]*){3,}', '\n\n', txt)
    # txt = re.sub(r'[-*] #', '#', txt)
    return txt


def debug(msg: str = '', exception=False):
    baseScrapper.debug(DEBUG, msg, exception)
