import math
import time
import re
from selenium.common.exceptions import NoSuchElementException
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import htmlToMarkdown, join, validate
from ai_job_search.scrapper.util import getAndCheckEnvVars
from ai_job_search.tools.terminalColor import green, red, yellow
from .seleniumUtil import SeleniumUtil
from ai_job_search.tools.mysqlUtil import MysqlUtil
from .selectors.infojobsSelectors import (
    CSS_SEL_JOB_DESCRIPTION,
    CSS_SEL_JOB_EASY_APPLY,
    CSS_SEL_JOB_REQUIREMENTS,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND,
    CSS_SEL_COMPANY,
    CSS_SEL_LOCATION,
    CSS_SEL_JOB_TITLE,
    CSS_SEL_JOB_LINK,
    CSS_SEL_NEXT_PAGE_BUTTON,
    LOGIN_PAGE)


USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("INFOJOBS")

# Set to True to stop selenium driver navigating if any error occurs
DEBUG = True

JOBS_X_PAGE = 25

print('seleniumInfojobs init')
selenium = None
mysql = None


def run(seleniumUtil: SeleniumUtil):
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    selenium = seleniumUtil
    try:
        mysql = MysqlUtil()
        login()
        # selenium.waitUntilPageContains(
        #     'https://accounts.infojobs.net/security/accounts/login/run', 60)
        selenium.waitUntilPageUrlContains(
            'https://www.infojobs.net/error404.xhtml', 60)
        input(yellow('Solve a security filter and press a key...'))
        for keywords in JOBS_SEARCH.split(','):
            searchJobs(keywords.strip())
    finally:
        mysql.close()


def login():
    try:
        selenium.loadPage(LOGIN_PAGE)
        selenium.sendKeys('#email', USER_EMAIL)
        selenium.sendKeys('#id-password', USER_PWD)
        selenium.scrollIntoView('#didomi-notice-agree-button > span')
        selenium.waitAndClick('#didomi-notice-agree-button > span')
        selenium.waitAndClick('#idSubmitButton')
    except Exception as ex:
        print(ex)
        debug('Login did not work')


def getUrl(keywords):
    return join('https://www.infojobs.net/jobsearch/search-results/list.xhtml',
                f'?keyword={keywords}&searchByType=country&teleworkingIds=2',
                '&segmentId=&page=1&sortBy=PUBLICATION_DATE',
                '&onlyForeignCountry=false&countryIds=17&sinceDate=_7_DAYS')
    # '&'.join([
    #     f'keywords={quote(keywords)}', f'f_WT={remote}',
    #     f'geoId={location}', f'f_TPR={f_TPR}']))


def replaceIndex(cssSelector: str, idx: int):
    return cssSelector.replace('##idx##', str(idx))


def getTotalResultsFromHeader(keywords: str) -> int:
    total = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
    print(green('-'*150))
    print(green(join(f'{total} total results for search: {keywords}')))
    #  f'(remote={remote}, location={location}, last={f_TPR})')))
    print(green('-'*150))
    return int(total)


def summarize(keywords, totalResults, currentItem):
    print('-'*150)
    print(f'Loaded {currentItem} of {totalResults} total results for',
          f'search: {keywords}')
    #   f'(remote={remote} location={location} last={f_TPR})')
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


def loadJobDetail(jobExists: bool, cssSel):
    # first job in page loads automatically
    # if job exists in DB no need to load details (rate limit)
    if jobExists:
        return
    print(yellow('loading...'), end='')
    selenium.waitAndClick(cssSel)


def jobExistsInDB(url):
    jobId = getJobId(url)
    return (jobId, mysql.getJob(jobId) is not None)


def getJobId(url: str):
    return re.sub(r'.+/of-([^?/]+).*', r'\1', url)


def getJobUrlShort(url: str):
    return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)


def searchJobs(keywords: str):
    try:
        url = getUrl(keywords)
        selenium.loadPage(url)
        selenium.waitUntilPageIsLoaded()
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
    loaded = False
    try:
        cssSel = scrollJobsList(idx)
        url = selenium.getAttr(cssSel, 'href')
        jobId, jobExists = jobExistsInDB(url)
        loadJobDetail(jobExists, cssSel)
        loaded = not jobExists
    except NoSuchElementException as ex:
        debug("NoSuchElement in loadAndProcessRow " +
              red(f'ERROR (loadJob): {ex}'))
    if jobExists:
        print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
    elif loaded:
        processRow(idx, url)
        selenium.back()


def processRow(idx, url, retry=True):
    try:
        title = selenium.getText(CSS_SEL_JOB_TITLE)
        company = selenium.getText(CSS_SEL_COMPANY)
        location = selenium.getText(CSS_SEL_LOCATION)
        jobId = getJobId(url)
        html = selenium.getHtml(CSS_SEL_JOB_REQUIREMENTS)
        html += selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        md = htmlToMarkdown(html)
        # easyApply: there are 2 buttons
        easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
        print(f'{jobId}, {title}, {company}, {location}, ',
              f'easy_apply={easyApply} - ', end='')
        if validate(title, url, company, md, DEBUG):
            if mysql.insert((jobId, title, company, location, url, md,
                             easyApply, 'Infojobs')):  # TODO: move to declaration in all scrappers
                print(green('INSERTED!'), end='')
        elif retry:
            print(yellow('waiting 10 secs... & retrying... '))
            time.sleep(10)
            processRow(idx, url, retry=False)
            return
    except Exception as ex:
        debug('processRow Exception -> ' + red(f'ERROR: {ex}'))
    print()


def debug(msg: str = ''):
    baseScrapper.debug(DEBUG, msg)
