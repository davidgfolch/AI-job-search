import math
import time
import re
import traceback
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import (
    htmlToMarkdown, join, printScrapperTitle, validate)
from ai_job_search.scrapper.util import getAndCheckEnvVars
from ai_job_search.tools.terminalColor import green, red, yellow
from .seleniumUtil import SeleniumUtil, sleep
from ai_job_search.tools.mysqlUtil import MysqlUtil
from .selectors.infojobsSelectors import (
    CSS_SEL_COMPANY2,
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

print('seleniumInfojobs init')
selenium = None
mysql = None


def run():
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    printScrapperTitle('Infojobs')
    try:
        selenium = SeleniumUtil()
        mysql = MysqlUtil()
        login()
        securityFilter()
        selenium.waitUntilPageUrlContains(
            'https://www.infojobs.net/error404.xhtml', 60)
        input(yellow('Solve a security filter and press a key...'))
        for keywords in JOBS_SEARCH.split(','):
            searchJobs(keywords.strip())
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
    selenium.scrollIntoView('#didomi-notice-agree-button > span')
    sleep(2, 6, disableWait)
    selenium.waitAndClick('#didomi-notice-agree-button > span')
    sleep(2, 6, disableWait)
    selenium.sendKeys('#email', USER_EMAIL,
                      keyByKeyTime=None if disableWait else (0.01, 0.1))
    sleep(2, 6, disableWait)
    selenium.sendKeys('#id-password', USER_PWD,
                      keyByKeyTime=None if disableWait else (0.03, 0.6))
    sleep(2, 6, disableWait)
    selenium.waitAndClick('#idSubmitButton')


def securityFilter():
    selenium.waitUntilPageIsLoaded()
    # contacta con nosotros
    selenium.waitAndClick(CSS_SEL_SECURITY_FILTER1)
    selenium.waitAndClick(CSS_SEL_SECURITY_FILTER2)


def getUrl(keywords):
    return join('https://www.infojobs.net/jobsearch/search-results/list.xhtml',
                f'?keyword={keywords}&searchByType=country&teleworkingIds=2',
                '&segmentId=&page=1&sortBy=PUBLICATION_DATE',
                '&onlyForeignCountry=false&countryIds=17&sinceDate=_7_DAYS')


def replaceIndex(cssSelector: str, idx: int):
    return cssSelector.replace('##idx##', str(idx))


def getTotalResultsFromHeader(keywords: str) -> int:
    total = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
    print(green('-'*150))
    print(green(join(f'{total} total results for search: {keywords}')))
    print(green('-'*150))
    return int(total)


def summarize(keywords, totalResults, currentItem):
    print('-'*150)
    print(f'Loaded {currentItem} of {totalResults} total results for',
          f'search: {keywords}')
    print('-'*150)
    print()


def scrollJobsList(idx):
    if idx < JOBS_X_PAGE-3:  # scroll to job link
        i = 0
        while i <= idx:
            # in last page could not exist
            li = selenium.getElms(CSS_SEL_JOB_LI)[i]
            if not selenium.scrollIntoView_noError(li):
                print(yellow(' waiting 5 secs... & retrying... '), end='')
                time.sleep(5)
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
        page = 0
        currentItem = 0
        while currentItem < totalResults:
            page += 1
            printPage(page, totalPages, keywords)
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
    except Exception as ex:
        if DEBUG:
            raise ex
        debug(red(f'ERROR: {ex}'))


def getJobLinkElement(idx):
    liElm = selenium.getElms(CSS_SEL_JOB_LI)[idx]
    return selenium.getElmOf(liElm, CSS_SEL_JOB_LINK)


def loadAndProcessRow(idx, retry=True):
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
        loadJobDetail(jobExists, jobLinkElm)
        processed = True
    except IndexError as ex:
        print(yellow("WARNING: could not get all items per page, that's ",
                     f"expected because not always has {JOBS_X_PAGE}: {ex}"))
    except Exception as ex:
        print(red(f'ERROR: {ex}'))
        debug(red(traceback.format_exc()))
    if processed:
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


def processRow(url):
    # try:
    title = selenium.getText(CSS_SEL_JOB_TITLE)
    company = getCompany()
    location = selenium.getText(CSS_SEL_LOCATION)
    jobId = getJobId(url)
    html = selenium.getHtml(CSS_SEL_JOB_REQUIREMENTS)
    html += selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
    # TODO: Infojobs  "Conocimientos necesarios" are relative url links,
    # implement tree visitor for a.href (and img.src)
    # https://stackoverflow.com/questions/54920208/python-markdown-how-can-i-config-base-url-for-media-when-markdown-string-into-h
    md = htmlToMarkdown(html)
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


def getCompany():
    elms = selenium.getElms(CSS_SEL_COMPANY)
    if len(elms) > 0:
        return elms[0].text
    return selenium.getText(CSS_SEL_COMPANY2)


def printPage(page, totalPages, keywords):
    print(green(f'{WEB_PAGE} Starting page {page} of {totalPages} ',
                f'search={keywords} {"-"*100}'))


def debug(msg: str = ''):
    baseScrapper.debug(DEBUG, msg)
