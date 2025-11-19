import math
import re
from urllib.parse import quote
from selenium.common.exceptions import NoSuchElementException

from . import baseScrapper
from .baseScrapper import getAndCheckEnvVars, htmlToMarkdown, join, printPage, printScrapperTitle, validate
from commonlib.terminalColor import green, magenta, printHR, red, yellow
from commonlib.decorator.retry import retry
from commonlib.util import getDatetimeNowStr
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs
from .seleniumUtil import SeleniumUtil
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
# f_TPR = 'r604800'  # last week
# f_TPR = 'r2592000'  # last month
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False

WEB_PAGE = 'Linkedin'
JOBS_X_PAGE = 25

print('Linkedin scrapper init')
selenium: SeleniumUtil
mysql: MysqlUtil


def run(seleniumUtil: SeleniumUtil, preloadPage: bool):
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    selenium = seleniumUtil
    printScrapperTitle('LinkedIn', preloadPage)
    if preloadPage:
        login()
        print(yellow('Waiting for LinkedIn to redirect to feed page... (Maybe you need to solve a security filter first)'))
        selenium.waitUntilPageUrlContains('https://www.linkedin.com/feed/', 60)
        return
    with MysqlUtil() as mysql:
        # TODO: save search keywords in DB
        # TODO: additionally set search ranking?
        for keywords in JOBS_SEARCH.split(','):
            searchJobs(keywords.strip())


def login():
    selenium.loadPage('https://www.linkedin.com/login')
    selenium.waitUntilPageIsLoaded()
    if selenium.getUrl().find('linkedin.com/feed/') > -1:
        return  # linkedin redirects to feed if previous login done with same selenium driver
    selenium.sendKeys('#username', USER_EMAIL)
    selenium.sendKeys('#password', USER_PWD)
    try:
        selenium.checkboxUnselect('div.remember_me__opt_in input')
    except Exception as e:
        print(red(str(e)))
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
        baseScrapper.debug(DEBUG, f'checkResults -> no results for search={keywords}', False)
        return False
    return True


def replaceIndex(cssSelector: str, idx: int):
    return cssSelector.replace('##idx##', str(idx))


@retry(exception=NoSuchElementException)
def getTotalResultsFromHeader(keywords: str) -> int:
    total = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0].replace('+', '')  # can be 100+
    printHR(green)
    print(green(join(f'{total} total results for search: {keywords}',
                     f'(remote={remote}, location={location}, last={f_TPR})')))
    printHR(green)
    return int(total.replace('+', ''))


def summarize(keywords, totalResults, currentItem):
    printHR()
    print(f'{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords}',
          f'(remote={remote} location={location} last={f_TPR})')
    printHR()
    print()


def scrollJobsList(idx):
    cssSel = replaceIndex(CSS_SEL_JOB_LINK, idx)
    try:
        selenium.scrollIntoView(cssSel)
    except NoSuchElementException:
        scrollJobsListRetry(idx)
        selenium.scrollIntoView(cssSel)
    selenium.moveToElement(selenium.getElm(cssSel))
    selenium.waitUntilClickable(cssSel)
    return cssSel


@retry()
def scrollJobsListRetry(idx):
    """Scroll to job list item idx-1, idx, idx+1 to load lazy items (class name changes in linked in and is not visible)"""
    for i in range(idx, idx+1):
        cssSelI = replaceIndex(CSS_SEL_JOB_LI_IDX, i)
        selenium.scrollIntoView(cssSelI)
        selenium.moveToElement(selenium.getElm(cssSelI))
        selenium.waitUntilClickable(replaceIndex(CSS_SEL_JOB_LINK, i))


@retry(exception=NoSuchElementException, raiseException=False)
def clickNextPage():
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
    return True


def loadJobDetail(jobExists: bool, idx: int, cssSel):
    # first job in page loads automatically
    # if job exists in DB no need to load details (rate limit)
    if jobExists or idx == 1:
        return
    print(yellow('loading...'), end='', flush=True)
    selenium.waitAndClick(cssSel)


def jobExistsInDB(cssSel):
    url = selenium.getAttr(cssSel, 'href')
    jobId = getJobId(url)
    return (jobId, mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, jobId) is not None)


def getJobId(url: str) -> int:
    return int(re.sub(r'.*/jobs/view/([^/]+)/.*', r'\1', url))


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
        selenium.waitAndClick_noError(CSS_SEL_MESSAGES_HIDE, 'Could not collapse messages')
        totalResults = getTotalResultsFromHeader(keywords)
        totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        page = 1
        currentItem = 0
        while True:
            printPage(WEB_PAGE, page, totalPages, keywords)
            rowErrors = 0
            for idx in range(1, JOBS_X_PAGE+1):
                if currentItem >= totalResults:
                    break  # exit for
                currentItem += 1
                print(green(f'pg {page} job {idx} - '), end='', flush=True)
                if not loadAndProcessRow(idx):
                    rowErrors += 1
                if rowErrors > 1:  # exit page loop, some pages has less items
                    break
            if currentItem >= totalResults or page >= totalPages or not clickNextPage():
                break  # exit while
            page += 1
            selenium.waitUntilPageIsLoaded()
        summarize(keywords, totalResults, currentItem)
    except Exception:
        baseScrapper.debug(DEBUG, '', True)


def loadAndProcessRow(idx):
    jobExists = False
    try:
        cssSel = scrollJobsList(idx)
        jobId, jobExists = jobExistsInDB(cssSel)
        loadJobDetail(jobExists, idx, cssSel)
    except NoSuchElementException as ex:
        baseScrapper.debug(DEBUG, "NoSuchElement in loadAndProcessRow " + red(f'ERROR (loadJob): {ex.msg}'))
        print()
        return False
    if jobExists:
        print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
    else:
        processRow(idx)
        print()
    return True


def processUrl(url: str):
    global selenium, mysql
    with MysqlUtil() as mysql, SeleniumUtil() as selenium:
        selenium.loadPage(url)
        selenium.waitUntilPageIsLoaded()
        processRow(None)


@retry(exception=ValueError)
def processRow(idx):
    isDirectUrlScrapping = idx is None
    try:
        title, company, location, url, html = getJobDataInDetailPage() if isDirectUrlScrapping else getJobDataInList(idx)
        jobId = getJobId(url)
        md = htmlToMarkdown(html)
        easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0  # easyApply: there are 2 buttons
        print(f'{jobId}, {title}, {company}, {location}, easy_apply={easyApply} - ', end='', flush=True)
        if validate(title, url, company, md, DEBUG):
            if isDirectUrlScrapping and mysql.jobExists(str(jobId)):
                printJob(title, company, location, url, jobId, html, md)
            elif id := mysql.insert((jobId, title, company, location, url, md, easyApply, WEB_PAGE)):
                print(green(f'INSERTED {id}!'), end='', flush=True)
                mergeDuplicatedJobs(mysql, getSelect())
        else:
            raise ValueError('Validation failed')
    except (ValueError, KeyboardInterrupt) as e:
        raise e
    except Exception:
        baseScrapper.debug(DEBUG, '', True)

def printJob(title, company, location, url, jobId, html, md):
    print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
    print(yellow(f'TITLE={title}'))
    print(yellow(f'COMPANY={company}'))
    print(yellow(f'LOCATION={location}'))
    print(yellow(f'URL={url}'))
    print(yellow(f'HTML:\n', magenta(html)))
    print(yellow(f'MARKDOWN:\n', magenta(md)))


def getJobDataInDetailPage():
    # TODO: finish this, maybe update DB
    selenium.waitUntil_presenceLocatedElement('section[aria-modal=true][role=dialog]')
    selenium.sendEscapeKey()
    selenium.waitUntilClickable('section.top-card-layout h1')
    title = selenium.getText('section.top-card-layout h1')
    company = selenium.getText('section.top-card-layout h4 a.topcard__org-name-link')
    location = selenium.getText('section.top-card-layout h4 span')
    selenium.waitAndClick('button.show-more-less-html__button--more')
    url = selenium.getUrl()
    html = selenium.getHtml('div.show-more-less-html__markup')
    return title, company, location, url, html


def getJobDataInList(idx):
    liPrefix = replaceIndex(CSS_SEL_JOB_LI_IDX, idx)
    title = selenium.getText(f'{liPrefix} {LI_JOB_TITLE_CSS_SUFFIX}')
    company = selenium.getText(f'{liPrefix} {CSS_SEL_COMPANY}')
    location = selenium.getText(f'{liPrefix} {CSS_SEL_LOCATION}')
    selenium.waitUntilClickable(CSS_SEL_JOB_HEADER)
    url = getJobUrlShort(selenium.getAttr(CSS_SEL_JOB_HEADER, 'href'))
    html = selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
    return title, company, location, url, html
