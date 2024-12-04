import math
import os
import time
from urllib.parse import quote
import re
from dotenv import load_dotenv
import markdownify
from selenium.common.exceptions import NoSuchElementException
from ai_job_search.terminalColor import green, red, yellow
from seleniumUtil import SeleniumUtil
from ai_job_search.tools.mysqlUtil import MysqlUtil
from seleniumLinkedinSelectors import (
    CSS_SEL_GLOBAL_ALERT_HIDE,
    CSS_SEL_JOB_DESCRIPTION,
    CSS_SEL_JOB_EASY_APPLY,
    CSS_SEL_JOB_HEADER,
    CSS_SEL_NO_RESULTS,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND,
    CSS_SEL_JOB_LI_IDX,
    CSS_SEL_SUBTITLE,
    CSS_SEL_CAPTION,
    LI_JOB_TITLE_CSS_SUFFIX,
    CSS_SEL_JOB_LINK,
    CSS_SEL_NEXT_PAGE_BUTTON,
    CSS_SEL_MESSAGES_HIDE)

load_dotenv()


USER_EMAIL = os.environ.get("LINKEDIN_EMAIL")
USER_PWD = os.environ.get("LINKEDIN_PWD")
JOBS_SEARCH = os.environ.get("JOBS_SEARCH")

if not USER_EMAIL or not USER_PWD or not JOBS_SEARCH:
    print(yellow('Please read README.md first'))
    print(yellow('Set up .venv file with USER_EMAIL, USER_PWD & JOBS_SEARCH'))
    exit()

remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
# Spain if you need other make a manual search and get your country code
location = '105646813'
f_TPR = 'r86400'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False

JOBS_X_PAGE = 25

print('seleniumLinkedin init')
selenium = None
mysql = None


def run(seleniumUtil: SeleniumUtil):
    """Login, process jobs search paginated list results"""
    global selenium, mysql
    selenium = seleniumUtil
    try:
        mysql = MysqlUtil()
        login()
        print(yellow('Waiting for LinkedIn to redirect to feed page...',
                     '(Maybe you need to solve a security filter first)'))
        selenium.waitUntilPageIs('https://www.linkedin.com/feed/', 60)
        # TODO: save search keywords in DB
        # TODO: additionally set search ranking?
        for keywords in JOBS_SEARCH.split(','):
            searchJobs(keywords.strip())
    finally:
        mysql.close()


def login():
    selenium.loadPage('https://www.linkedin.com/login')
    selenium.sendKeys('#username', USER_EMAIL)
    selenium.sendKeys('#password', USER_PWD)
    try:
        selenium.checkboxUnselect('div.remember_me__opt_in input')
    except Exception as e:
        print(e)
    selenium.waitAndClick('form button[type=submit]')
    return selenium


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
    print(green('-'*150))
    print(green(join(f'{total} total results for search: {keywords}',
                     f'(remote={remote}, location={location}, last={f_TPR})')))
    print(green('-'*150))
    return int(total)


def summarize(keywords, totalResults, currentItem):
    print('-'*150)
    print(f'Loaded {currentItem} of {totalResults} total results for',
          f'search: {keywords}',
          f'(remote={remote} location={location} last={f_TPR})')
    print('-'*150)
    print()


def scrollJobsList(idx):
    cssSel = replaceIndex(CSS_SEL_JOB_LINK, idx)
    if idx < JOBS_X_PAGE-3:  # scroll to job link
        # in last page could not exist
        if not selenium.scrollIntoView_noError(cssSel):
            print(yellow(' waiting 10 secs... & retrying... '))
            time.sleep(10)
            selenium.scrollIntoView_noError(cssSel)
    selenium.waitUntilClickable(cssSel)
    return cssSel


def printPage(page, totalPages, keywords):
    print(green(f'Starting page {page} of {totalPages} ',
                f'search={keywords} {"-"*100}'))


def clickNextPage(retry=True):
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    try:
        selenium.waitAndClick(
            CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
        return True
    except NoSuchElementException:
        if retry:
            debug("retry clickNextPage")
            clickNextPage(False)
        return False


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
    return (jobId, mysql.getJob(jobId) is not None)


def getJobId(url: str):
    return re.sub(r'.*/jobs/view/([^/]+)/.*', r'\1', url)


def getJobUrlShort(url: str):
    return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)


def searchJobs(keywords: str):
    try:
        url = getUrl(keywords)
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
        printPage(page, totalPages, keywords)
        while True:
            for idx in range(1, JOBS_X_PAGE+1):
                if currentItem >= totalResults:
                    break  # exit for
                currentItem += 1
                print(green(f'pg {page} job {idx} - '), end='')
                loadAndProcessRow(idx)
            if currentItem >= totalResults:
                break  # exit while
            if not clickNextPage():
                break  # exit while
            page += 1
            printPage(page, totalPages, keywords)
            selenium.waitUntilPageIsLoaded()
        summarize(keywords, totalResults, currentItem)
    except Exception as ex:
        debug(red(f'ERROR: {ex}'))


def loadAndProcessRow(idx):
    try:
        cssSel = scrollJobsList(idx)
        jobId, jobExists = jobExistsInDB(cssSel)
        loadJobDetail(jobExists, idx, cssSel)
    except NoSuchElementException as ex:
        debug("NoSuchElement in loadAndProcessRow " +
              red(f'ERROR (loadJob): {ex}'))
    if jobExists:
        print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
    else:
        processRow(idx)


def processRow(idx, retry=True):
    # TODO: CSS_SEL_JOB_CLOSED -> No longer accepting applications
    # https://www.linkedin.com/jobs/view/4057715315/
    # TODO: AI -> Language ignore (german f.ex.)
    try:
        liPrefix = replaceIndex(CSS_SEL_JOB_LI_IDX, idx)
        title = selenium.getText(f'{liPrefix} {LI_JOB_TITLE_CSS_SUFFIX}')
        company = selenium.getText(f'{liPrefix} {CSS_SEL_SUBTITLE}')
        location = selenium.getText(f'{liPrefix} {CSS_SEL_CAPTION}')
        selenium.waitUntilClickable(CSS_SEL_JOB_HEADER)
        url = getJobUrlShort(selenium.getAttr(CSS_SEL_JOB_HEADER, 'href'))
        jobId = getJobId(url)
        html = selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        md = markdownify.markdownify(html)
        # easyApply: there are 2 buttons
        ea = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
        print(f'{jobId}, {title}, {company}, {location}, ',
              f'easyApply={ea} - ', end='')
        if validate(title, url, company, md):
            if mysql.insert((jobId, title, company, location, url, md, ea)):
                print(green('INSERTED!'), end='')
        elif retry:
            print(yellow('waiting 10 secs... & retrying... '))
            time.sleep(10)
            processRow(idx, retry=False)
            return
    except Exception as ex:
        debug('processRow Exception -> ' + red(f'ERROR: {ex}'))
    print()


def validate(title: str, url: str, company: str, markdown: str):
    if not (title.strip() and url and company and
            re.sub(r'\n', '', markdown, re.MULTILINE).strip()):
        markdown = markdown.split('\n')[0]
        debug("validate -> " +
              red('ERROR: One or more required fields are empty, ',
                  'NOT inserting into DB:',
                  f'title={title}, company={company}, ',
                  f'location={location},  markdown={markdown}...') +
              yellow(f' -> Url: {url}'))
        return False
    return True


def debug(msg: str = ''):
    if DEBUG:
        input(f" (debug active) {msg}, press a key")
    else:
        print(msg, end='')


def join(*str: str) -> str:
    return ''.join(str)
