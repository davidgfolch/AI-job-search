import math
import time
import re
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import (
    htmlToMarkdown, join, printPage, printScrapperTitle, validate)
from ai_job_search.tools.terminalColor import green, printHR, yellow
from ai_job_search.tools.util import getAndCheckEnvVars
from ai_job_search.viewer.util.decorator.retry import retry
from .seleniumUtil import SeleniumUtil, sleep
from ai_job_search.tools.mysqlUtil import MysqlUtil
from .selectors.infojobsSelectors import (
    CSS_SEL_JOB_DESCRIPTION,
    CSS_SEL_JOB_EASY_APPLY,
    CSS_SEL_JOB_LI,
    CSS_SEL_JOB_REQUIREMENTS,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND,
    CSS_SEL_COMPANY,
    CSS_SEL_LOCATION,
    CSS_SEL_JOB_TITLE,
    CSS_SEL_JOB_LINK,
    CSS_SEL_NEXT_PAGE_BUTTON,
    CSS_SEL_SECURITY_FILTER1,
    CSS_SEL_SECURITY_FILTER2,
    LOGIN_PAGE)


USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("INFOJOBS")

# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False

WEB_PAGE = 'Infojobs'
JOBS_X_PAGE = 22  # NOT ALWAYS, SOMETIMES LESS REGARDLESS totalResults

LOGIN_WAIT_DISABLE = True

print('Infojobs scrapper init')
selenium = None
mysql = None


def run():
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    printScrapperTitle('Infojobs')
    try:
        selenium = SeleniumUtil()
        mysql = MysqlUtil()
        # login()
        # securityFilter()
        # selenium.waitUntilPageUrlContains(
        # 'https://www.infojobs.net/error404.xhtml', 60)
        # input(yellow('Solve a security filter and press a key...'))
        for i, keywords in enumerate(JOBS_SEARCH.split(',')):
            searchJobs(i, keywords.strip())
    finally:
        mysql.close()
        selenium.close()


def login():
    # FIXME: AVOID ROBOT SECURITY FILTER, example with BeautifulSoup:
    # FIXME: https://github.com/ander-elkoroaristizabal/InfojobsScraper
    # slow write login to avoid security robot filter don't work
    selenium.loadPage(LOGIN_PAGE)
    disableWait = LOGIN_WAIT_DISABLE
    sleep(4, 6, disableWait)
    acceptCookies()
    selenium.sendKeys('#email', USER_EMAIL,
                      keyByKeyTime=None if disableWait else (0.01, 0.1))
    sleep(2, 6, disableWait)
    selenium.sendKeys('#id-password', USER_PWD,
                      keyByKeyTime=None if disableWait else (0.03, 0.6))
    sleep(2, 6, disableWait)
    selenium.waitAndClick('#idSubmitButton')


def acceptCookies():
    selenium.scrollIntoView('#didomi-notice-agree-button > span')
    sleep(2, 6)
    selenium.waitAndClick('#didomi-notice-agree-button > span')
    sleep(2, 6)


def securityFilter():
    selenium.waitUntilPageIsLoaded()
    sleep(4, 4)
    # selenium.waitUntil_presenceLocatedElement(CSS_SEL_SECURITY_FILTER1)
    # contacta con nosotros
    selenium.waitAndClick(CSS_SEL_SECURITY_FILTER1)
    selenium.waitAndClick(CSS_SEL_SECURITY_FILTER2)
    input(yellow('Solve a security filter and press a key...'))
    sleep(4, 4)
    acceptCookies()


def getUrl(keywords):
    return join('https://www.infojobs.net/jobsearch/search-results/list.xhtml',
                f'?keyword={keywords}&searchByType=country&teleworkingIds=2',
                '&segmentId=&page=1&sortBy=PUBLICATION_DATE',
                '&onlyForeignCountry=false&countryIds=17&sinceDate=_7_DAYS')


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
    print(f'Loaded {currentItem} of {totalResults} total results for',
          f'search: {keywords}')
    printHR()
    print()


def scrollToBottom():
    """ pre scroll to bottom to force load of li's """
    print("scrollToBottom... ", end='')
    # this this can contain "pagination" or "Nueva busqueda" when no pagination exists
    selenium.scrollIntoView(
        'div.ij-SearchListingPageContent-main main > div')
    sleep(3, 3)


@retry(retries=2, delay=5)
def scrollJobsList(idx):
    lis = selenium.getElms(CSS_SEL_JOB_LI)
    if (idx >= len(lis)):
        scrollToBottom()
        lis = selenium.getElms(CSS_SEL_JOB_LI)
    for i in range(0, idx+1):
        li = lis[i]
        selenium.scrollIntoView(li)


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
    return (jobId, mysql.getJob(jobId) is not None)


def getJobId(url: str):
    return re.sub(r'.+/of-([^?/]+).*', r'\1', url)


def getJobUrlShort(url: str):
    return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)


def searchJobs(index: int, keywords: str):
    try:
        url = getUrl(keywords)
        selenium.loadPage(url)
        selenium.waitUntilPageIsLoaded()
        if index == 0:
            securityFilter()
            selenium.waitUntilPageUrlContains(
                'https://www.infojobs.net/jobsearch/search-results', 60)
            # selenium.loadPage(url)
            # selenium.waitUntilPageIsLoaded()
        totalResults = getTotalResultsFromHeader(keywords)
        totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        page = 0
        currentItem = 0
        while currentItem < totalResults:
            page += 1
            printPage(WEB_PAGE, page, totalPages, keywords)
            idx = 0
            while idx < JOBS_X_PAGE and currentItem < totalResults:
                print(green(f'pg {page} job {idx+1} - '), end='')
                if loadAndProcessRow(idx):
                    currentItem += 1
                print()
                idx += 1
            if currentItem < totalResults:
                if clickNextPage():
                    selenium.waitUntilPageIsLoaded()
                    time.sleep(5)
                else:
                    break  # exit while
        summarize(keywords, totalResults, currentItem)
    except Exception:
        debug(exception=True)


def getJobLinkElement(idx):
    liElm = selenium.getElms(CSS_SEL_JOB_LI)[idx]
    return selenium.getElmOf(liElm, CSS_SEL_JOB_LINK)


@retry(retries=1, delay=5, raiseException=False)
def loadAndProcessRow(idx) -> bool:
    processed = False
    jobExists = False
    try:
        scrollJobsList(idx)
        # pagination not always contains all JOBS_X_PAGE
        jobLinkElm: WebElement = getJobLinkElement(idx)
        url = jobLinkElm.get_attribute('href')
        jobId, jobExists = jobExistsInDB(url)
        if jobExists:
            print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'),
                  end='')
            return True
        loadJobDetail(jobLinkElm)
        processed = True
    except IndexError as ex:
        debug(yellow("WARNING: could not get all items per page, that's ",
                     f"expected because not always has {JOBS_X_PAGE}: {ex}"))
    if processed:
        if not processRow(url):
            selenium.back()
            raise ValueError('Validation failed')
        selenium.back()
    return processed


@retry()
def processRow(url):
    sleep(5, 6)
    # try:
    title = selenium.getText(CSS_SEL_JOB_TITLE)
    company = selenium.getText(CSS_SEL_COMPANY)
    # company = selenium.getText(CSS_SEL_COMPANY2)
    location = selenium.getText(CSS_SEL_LOCATION)
    jobId = getJobId(url)
    html = selenium.getHtml(CSS_SEL_JOB_REQUIREMENTS)
    html += selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
    # TODO: Infojobs  "Conocimientos necesarios" are relative url links,
    # implement tree visitor for a.href (and img.src)
    # https://stackoverflow.com/questions/54920208/python-markdown-how-can-i-config-base-url-for-media-when-markdown-string-into-h
    md = htmlToMarkdown(html)
    md = postProcessMarkdown(md)
    # easyApply: there are 2 buttons
    easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
    print(f'{jobId}, {title}, {company}, {location}, ',
          f'easy_apply={easyApply} - ', end='')
    if validate(title, url, company, md, DEBUG):
        if mysql.insert((jobId, title, company, location, url, md,
                        easyApply, WEB_PAGE)):
            print(green('INSERTED!'), end='')
            return True
    return False


def postProcessMarkdown(md):
    txt = re.sub(r'\[([^\]]+)\]\(/ofertas-trabajo[^\)]+\)', r'\1', md)
    txt = re.sub(r'[\\]+-', '-', txt)
    txt = re.sub(r'[\\]+\.', '.', txt)
    txt = re.sub(r'-\n', '\n', txt)
    txt = re.sub(r'(\n[  ]*){3,}', '\n\n', txt)
    txt = re.sub(r'[-*] #', '#', txt)
    return txt


def debug(msg: str = '', exception=False):
    baseScrapper.debug(DEBUG, msg, exception)
