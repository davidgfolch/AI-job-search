import math
from urllib.parse import quote
import re
from selenium.common.exceptions import NoSuchElementException
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import (
    htmlToMarkdown, join, printPage,
    printScrapperTitle, validate)
from ai_job_search.tools.terminalColor import (
    green, printHR, red, yellow)
from ai_job_search.tools.util import getAndCheckEnvVars
from ai_job_search.tools.decorator.retry import retry
from ai_job_search.viewer.clean.mergeDuplicates import (
    getSelect, mergeDuplicatedJobs)
from .seleniumUtil import SeleniumUtil
from ai_job_search.tools.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from .selectors.linkedinSelectors import (
    # CSS_SEL_GLOBAL_ALERT_HIDE,
    CSS_SEL_JOB_DESCRIPTION,
    CSS_SEL_JOB_EASY_APPLY,
    CSS_SEL_JOB_HEADER,
    CSS_SEL_NO_RESULTS,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND,
    CSS_SEL_JOB_LI_IDX,
    CSS_SEL_COMPANY,
    CSS_SEL_LOCATION,
    LI_JOB_TITLE_CSS_SUFFIX,
    CSS_SEL_JOB_LINK,
    CSS_SEL_NEXT_PAGE_BUTTON,
    CSS_SEL_MESSAGES_HIDE)


USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("LINKEDIN")

remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
# Spain if you need other make a manual search and get your country code
location = '105646813'
f_TPR = 'r86400'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False

WEB_PAGE = 'Linkedin'
JOBS_X_PAGE = 25

print('Linkedin scrapper init')
selenium = None
mysql = None


def run():
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    printScrapperTitle('LinkedIn')
    with MysqlUtil() as mysql, SeleniumUtil() as selenium:
        login()
        print(yellow('Waiting for LinkedIn to redirect to feed page...',
                     '(Maybe you need to solve a security filter first)'))
        selenium.waitUntilPageUrlContains('https://www.linkedin.com/feed/', 60)
        # TODO: save search keywords in DB
        # TODO: additionally set search ranking?
        for keywords in JOBS_SEARCH.split(','):
            searchJobs(keywords.strip())


def login():
    selenium.loadPage('https://www.linkedin.com/login')
    selenium.sendKeys('#username', USER_EMAIL)
    selenium.sendKeys('#password', USER_PWD)
    try:
        selenium.checkboxUnselect('div.remember_me__opt_in input')
    except Exception as e:
        print(e)
    selenium.waitAndClick('form button[type=submit]')


def getUrl(keywords):
    return join('https://www.linkedin.com/jobs/search/?',
                '&'.join([
                    f'keywords={quote(keywords)}', f'f_WT={remote}',
                    f'geoId={location}', f'f_TPR={f_TPR}']))


def checkResults(keywords: str, url: str):
    noResultElm = selenium.getElms(CSS_SEL_NO_RESULTS)
    if len(noResultElm) > 0:
        print(Exception(
            join('No results for job search on linkedIn for',
                 f'keywords={keywords}', f'remote={remote}',
                 f'location={location}', f'old={f_TPR}', f'URL {url}')))
        debug(f'checkResults -> no results for search={keywords}')
        return False
    return True


def replaceIndex(cssSelector: str, idx: int):
    return cssSelector.replace('##idx##', str(idx))


def getTotalResultsFromHeader(keywords: str) -> int:
    total = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
    printHR(green)
    print(green(join(f'{total} total results for search: {keywords}',
                     f'(remote={remote}, location={location}, last={f_TPR})')))
    printHR(green)
    return int(total)


def summarize(keywords, totalResults, currentItem):
    printHR()
    print(f'Loaded {currentItem} of {totalResults} total results for',
          f'search: {keywords}',
          f'(remote={remote} location={location} last={f_TPR})')
    printHR()
    print()


def scrollJobsList(idx):
    cssSel = replaceIndex(CSS_SEL_JOB_LINK, idx)
    if idx < JOBS_X_PAGE-3:  # scroll to job link
        # in last page could not exist
        scrollJobsListRetry(cssSel)
    selenium.waitUntilClickable(cssSel)
    return cssSel


def scrollToBottom():
    selenium.scrollIntoView('#jobs-search-results-footer')


@retry(exceptionFnc=scrollToBottom)
def scrollJobsListRetry(cssSel):
    selenium.scrollIntoView(cssSel)


@retry(exception=NoSuchElementException, raiseException=False)
def clickNextPage():
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    selenium.waitAndClick(
        CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
    return True


def loadJobDetail(jobExists: bool, idx: int, cssSel):
    # first job in page loads automatically
    # if job exists in DB no need to load details (rate limit)
    if jobExists or idx == 1:
        return
    print(yellow('loading...'), end='')
    selenium.waitAndClick(cssSel)


def jobExistsInDB(cssSel):
    url = selenium.getAttr(cssSel, 'href')
    jobId = getJobId(url)
    return (jobId, mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, jobId) is not None)


def getJobId(url: str):
    return re.sub(r'.*/jobs/view/([^/]+)/.*', r'\1', url)


def getJobUrlShort(url: str):
    return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)


def searchJobs(keywords: str):
    try:
        print(yellow(f'Search keyword={keywords}'))
        url = getUrl(keywords)
        print(yellow(f'Loading page {url}'))
        selenium.loadPage(url)
        selenium.waitUntilPageIsLoaded()
        if not checkResults(keywords, url):
            return
        # selenium.waitAndClick_noError(CSS_SEL_GLOBAL_ALERT_HIDE,
        #                               'Could close global alert')
        selenium.waitAndClick_noError(CSS_SEL_MESSAGES_HIDE,
                                      'Could not collapse messages')
        totalResults = getTotalResultsFromHeader(keywords)
        totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        page = 1
        currentItem = 0
        while True:
            errors = 0
            printPage(WEB_PAGE, page, totalPages, keywords)
            for idx in range(1, JOBS_X_PAGE+1):
                if currentItem >= totalResults:
                    break  # exit for
                currentItem += 1
                print(green(f'pg {page} job {idx} - '), end='')
                ok = loadAndProcessRow(idx)
                errors += 0 if ok else 1
                if errors > 1:  # exit page loop, some pages has less items
                    break
            if currentItem >= totalResults:
                break  # exit while
            if not clickNextPage():
                break  # exit while
            page += 1
            selenium.waitUntilPageIsLoaded()
        summarize(keywords, totalResults, currentItem)
    except Exception as ex:
        debug(red(f'ERROR: {ex}'))


def loadAndProcessRow(idx):
    jobExists = False
    try:
        cssSel = scrollJobsList(idx)
        jobId, jobExists = jobExistsInDB(cssSel)
        loadJobDetail(jobExists, idx, cssSel)
    except NoSuchElementException as ex:
        debug("NoSuchElement in loadAndProcessRow " +
              red(f'ERROR (loadJob): {ex.msg}'))
        return False
    if jobExists:
        print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
    else:
        processRow(idx)
    return True


@retry(exception=ValueError)
def processRow(idx):
    # TODO: CSS_SEL_JOB_CLOSED -> No longer accepting applications
    # https://www.linkedin.com/jobs/view/4057715315/
    try:
        liPrefix = replaceIndex(CSS_SEL_JOB_LI_IDX, idx)
        title = selenium.getText(f'{liPrefix} {LI_JOB_TITLE_CSS_SUFFIX}')
        company = selenium.getText(f'{liPrefix} {CSS_SEL_COMPANY}')
        location = selenium.getText(f'{liPrefix} {CSS_SEL_LOCATION}')
        selenium.waitUntilClickable(CSS_SEL_JOB_HEADER)
        url = getJobUrlShort(selenium.getAttr(CSS_SEL_JOB_HEADER, 'href'))
        jobId = getJobId(url)
        html = selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        md = htmlToMarkdown(html)
        # easyApply: there are 2 buttons
        easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
        print(f'{jobId}, {title}, {company}, {location}, ',
              f'easy_apply={easyApply} - ', end='')
        if validate(title, url, company, md, DEBUG):
            if id := mysql.insert((jobId, title, company, location, url, md,
                                   easyApply, WEB_PAGE)):
                print(green(f'INSERTED {id}!'), end='')
                mergeDuplicatedJobs(mysql.fetchAll(getSelect()))
        else:
            raise ValueError('Validation failed')
    except ValueError as e:
        raise e
    except Exception as ex:
        debug('processRow Exception -> ' + red(f'ERROR: {ex}'))
    print()


def debug(msg: str = ''):
    baseScrapper.debug(DEBUG, msg)
