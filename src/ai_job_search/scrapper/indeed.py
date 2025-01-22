import time
import re
import traceback
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import (
    htmlToMarkdown, join, printPage, printScrapperTitle, validate)
from ai_job_search.tools.terminalColor import green, printHR, red, yellow
from ai_job_search.tools.util import getAndCheckEnvVars
from .seleniumUtil import SeleniumUtil
from ai_job_search.tools.mysqlUtil import MysqlUtil
from .selectors.indeedSelectors import (
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


USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("INDEED")

# Set to True to stop selenium driver navigating if any error occurs
DEBUG = True

WEB_PAGE = 'Indeed'
JOBS_X_PAGE = 15

LOGIN_WAIT_DISABLE = True

print('Indeed scrapper init')
selenium = None
mysql = None


def run():
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    printScrapperTitle('Indeed')
    try:
        selenium = SeleniumUtil()
        mysql = MysqlUtil()
        for i, keywords in enumerate(JOBS_SEARCH.split(',')):
            searchJobs(i, keywords.strip())
    finally:
        mysql.close()
        selenium.close()


def getUrl(keywords):
    return join('https://es.indeed.com/jobs',
                f'?q={keywords}&l=Espa%C3%B1a&fromage=1',
                '&sc=0kf%253Aattr(DSQF7)%253B&sort=date')


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


def scrollJobsList(idx):
    if idx < JOBS_X_PAGE-3:  # scroll to job link
        i = 0
        while i <= idx:
            # in last page could not exist
            li = selenium.getElms(CSS_SEL_JOB_LI)[i]
            selenium.scrollIntoView_noError(li)
            i += 1


def clickNextPage(retry=True):
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    try:
        selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
        return True
    except NoSuchElementException:
        if retry:
            # FIXME: implement as decorator:
            # https://github.com/indently/five_decorators/blob/main/decorators/001_retry.py
            debug("retry clickNextPage")
            return clickNextPage(False)
        return False


def loadJobDetail(jobExists: bool, jobLinkElm: WebElement):
    # first job in page loads automatically
    # if job exists in DB no need to load details (rate limit)
    print(yellow('loading...'), end='')
    jobLinkElm.click()


def jobExistsInDB(url):
    jobId = getJobId(url)
    return (jobId, mysql.getJob(jobId) is not None)


def getJobId(url: str):
    return re.sub(r'.+\?.*jk=([^&]+).*', r'\1', url)


def getJobUrlShort(url: str):
    return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)


def acceptCookies():
    selenium.waitAndClick_noError(
        '#onetrust-accept-btn-handler', 'Could not accept cookies')


def searchJobs(index: int, keywords: str):
    try:
        url = getUrl(keywords)
        selenium.loadPage(url)
        selenium.waitUntilPageIsLoaded()
        time.sleep(2)
        # NOTE: totalResults could be like +400, +50
        # totalResults = getTotalResultsFromHeader(keywords)
        # totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        acceptCookies()
        page = 0
        currentItem = 0
        totalResults = 0
        while True:
            page += 1
            printPage(WEB_PAGE, page, '?', keywords)
            idx = 0
            while idx < JOBS_X_PAGE:
                print(green(f'pg {page} job {idx+1} - '), end='')
                totalResults += 1
                if loadAndProcessRow(idx):
                    currentItem += 1
                print()
                idx += 1
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


def loadAndProcessRow(idx, retry=True):
    ignore = True
    jobExists = False
    try:
        scrollJobsList(idx)
        jobLinkElm: WebElement = getJobLinkElement(idx)
        url = jobLinkElm.get_attribute('href')
        jobId, jobExists = jobExistsInDB(url)
        # clean url just with jobId param
        url = f'https://es.indeed.com/viewjob?jk={jobId}'
        if jobExists:
            print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'),
                  end='')
            return True
        loadJobDetail(jobExists, jobLinkElm)
        time.sleep(3)
        ignore = False
    except IndexError as ex:
        print(yellow("WARNING: could not get all items per page, that's ",
                     f"expected because not always has {JOBS_X_PAGE}: {ex}"))
    except Exception as ex:
        print(red(f'ERROR: {ex}'))
        debug(red(traceback.format_exc()))
    if not ignore:
        if not processRow(url):
            print(red('Validation failed'))
            return loadAndProcessRow(idx, False)
        selenium.back()
        return True
    if retry:
        print(yellow('waiting 5 secs... & retrying... '), end='')
        time.sleep(5)
        return loadAndProcessRow(idx, False)
    return False


def processRow(url, retry=True):
    # try:
    title = selenium.getText(CSS_SEL_JOB_TITLE).removesuffix('\n- job post')
    company = selenium.getText(CSS_SEL_COMPANY)
    # company = selenium.getText(CSS_SEL_COMPANY2)
    location = selenium.getText(CSS_SEL_LOCATION)
    jobId = getJobId(url)
    selenium.scrollIntoView(CSS_SEL_JOB_REQUIREMENTS)
    selenium.waitUntil_presenceLocatedElement(CSS_SEL_JOB_REQUIREMENTS)
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
    if retry:
        return processRow(url, False)
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
