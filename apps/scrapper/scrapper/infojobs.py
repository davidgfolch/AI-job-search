import math
import time
import re
import traceback
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from .seleniumUtil import SeleniumUtil, sleep
from . import baseScrapper
from .baseScrapper import getAndCheckEnvVars, htmlToMarkdown, join, printPage, printScrapperTitle, removeLinks, validate
from commonlib.terminalColor import green, printHR, red, yellow
from commonlib.decorator.retry import retry
from commonlib.util import getDatetimeNowStr
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs
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
selenium: SeleniumUtil
mysql: MysqlUtil


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
    if not selenium.driverUtil.useUndetected:
        print(yellow('SOLVE A SECURITY FILTER in selenium webbrowser...'), end='')
        sleep(4, 4)
    selenium.scrollIntoView('#didomi-notice-agree-button > span')
    sleep(1, 3)
    selenium.waitAndClick('#didomi-notice-agree-button > span')
    sleep(2, 4)
    print()


def securityFilter():
    if selenium.driverUtil.useUndetected:
        acceptCookies()
        return
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
    return int(total.replace(',', ''))  # remove 1,200 comma


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
    # selenium.scrollToBottom()
    selenium.scrollProgressive(600)
    selenium.scrollProgressive(-1200)
    sleep(1, 2)


@retry(retries=5, delay=3, exception=NoSuchElementException, raiseException=False)
def clickNextPage():
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
    return True


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
            if not selenium.driverUtil.useUndetected:
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
                # Note JOBS_X_PAGE is not always exact
                print(green(f'pg {page} job {idx+1} - '), end='', flush=True)
                loadAndProcessRow(idx)
                currentItem += 1
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
        baseScrapper.debug(DEBUG, exception=True)


def loadSearchPage():
    if selenium.getUrl().find('infojobs.net') == -1:
        print(yellow(f'Loading search-jobs page'))
        selenium.loadPage('https://www.infojobs.net/')
        selenium.waitUntilPageIsLoaded()
    print(yellow(f'Click on search-jobs button'))
    clickOnSearchJobs()


def loadFilteredSearchResults(keywords: str):
    clickOnSearchJobs()
    if not selenium.sendKeys('.ij-SidebarFilter #fieldsetKeyword', keywords, keyByKeyTime=(0.1, 0.2), clear=True):
        print(yellow('Could not set search keyword, reloading search page'))
        clickOnSearchJobs(forcePageLoad=True)
        selenium.sendKeys('.ij-SidebarFilter #fieldsetKeyword', keywords, keyByKeyTime=(0.1, 0.2))
    sleep(0.5, 1)
    selenium.sendEscapeKey()
    sleep(0.5, 1)
    selenium.waitAndClick('.ij-SidebarFilter #buttonKeyword', scrollIntoView=True)
    sleep(1, 2)
    selenium.waitUntil_presenceLocatedElement('.ij-SidebarFilter input[type="radio"][value="_7_DAYS"]', timeout=5)
    selenium.waitAndClick('.ij-SidebarFilter input[type="radio"][value="_7_DAYS"]', scrollIntoView=True)
    sleep(1, 2)
    if selenium.getElms('.ij-OfferList-NoResults-title').__len__() > 0:
        print(yellow('No results for this search'))
        printHR()
        print()
        return False
    selenium.waitAndClick('.ij-SidebarFilter #check-teleworking--2', scrollIntoView=True)
    sleep(1, 2)
    return True


@retry(retries=10, delay=5, exceptionFnc=securityFilter)
def clickOnSearchJobs(forcePageLoad=False):
    if (not forcePageLoad) and selenium.getUrl().find('/ofertas-trabajo') > 0:
        return
    selenium.waitAndClick('header nav ul li a[href="/ofertas-trabajo"]', scrollIntoView=True)
    selenium.waitUntilPageIsLoaded()


@retry(retries=3, delay=1, exceptionFnc=scrollToBottom)
def scrollJobsList(idx):
    links = selenium.getElms(CSS_SEL_JOB_LINK)
    if idx >= len(links):  # if link not found, scroll all list to properly load dynamic links' class in DOM
        for li in selenium.getElms(CSS_SEL_JOB_LI)[len(links)-1:]:
            selenium.setAttr(li, 'style', (selenium.getAttr(li, 'style') or '')+'border: 5px solid red;')
            selenium.scrollIntoView(li)
            sleep(0.5, 1)
            selenium.setAttr(li, 'style', '')
        sleep(1, 2)
    selenium.scrollIntoView(selenium.getElms(CSS_SEL_JOB_LINK)[idx])


def loadAndProcessRow(idx) -> bool:
    try:
        if idx > 2:
            try:
                scrollJobsList(idx)
            except Exception:
                print(yellow(f'Could not scroll to link {idx+1}, IGNORING.'), end='')
                return False
        jobLinkElm: WebElement = selenium.getElms(CSS_SEL_JOB_LINK)[idx]
        url = jobLinkElm.get_attribute('href')
        jobId, jobExists = jobExistsInDB(url)
        if jobExists:
            print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'), end='')
            return True
        print(yellow('loading...'), end='')
        selenium.waitAndClick(jobLinkElm)
        if not processRow(url):
            raise ValueError('Validation failed')
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)
        return False
    finally:
        print(flush=True)
        if LIST_URL not in selenium.getUrl():
            selenium.back()
    return True


@retry(retries=3, delay=5)
def processRow(url):
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
        if id := mysql.insert((jobId, title, company, location, url, md, None, WEB_PAGE)):
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