import math
import time
import re
import traceback
from selenium.common.exceptions import NoSuchElementException
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import (
    htmlToMarkdown, printPage, printScrapperTitle, validate)
from ai_job_search.tools.terminalColor import green, printHR, red, yellow
from ai_job_search.tools.util import getAndCheckEnvVars, getEnv
from ai_job_search.viewer.util.decorator.retry import retry
from .seleniumUtil import SeleniumUtil, sleep
from ai_job_search.tools.mysqlUtil import MysqlUtil
from ai_job_search.scrapper.selectors.glassdoorSelectors import (
    CSS_SEL_COMPANY2,
    CSS_SEL_COOKIES_ACCEPT,
    CSS_SEL_DIALOG_CLOSE,
    CSS_SEL_INPUT_PASS,
    CSS_SEL_JOB_DESCRIPTION,
    CSS_SEL_JOB_EASY_APPLY,
    CSS_SEL_JOB_LI,
    CSS_SEL_NEXT_PAGE_BUTTON,
    CSS_SEL_PASSWORD_SUBMIT,
    CSS_SEL_SEARCH_RESULT_TOTAL,
    CSS_SEL_COMPANY,
    CSS_SEL_LOCATION,
    CSS_SEL_JOB_TITLE,
    LI_JOB_TITLE_CSS_SUFFIX)


SITE = "GLASSDOOR"
USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars(SITE)
JOBS_SEARCH_BASE_URL = getEnv(f'{SITE}_JOBS_SEARCH_BASE_URL')

DEBUG = False

WEB_PAGE = 'Glassdoor'
JOBS_X_PAGE = 30

print('Glassdoor scrapper init')
selenium = None
mysql = None


def run():
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    printScrapperTitle('Glassdoor')
    try:
        selenium = SeleniumUtil()
        mysql = MysqlUtil()
        login()
        for search in JOBS_SEARCH.split('|~|'):
            url = JOBS_SEARCH_BASE_URL.format(**{'search': search})
            print(yellow('Search list URL ', url))
            searchJobs(url)
    finally:
        mysql.close()
        selenium.close()


def login():
    try:
        selenium.loadPage('https://www.glassdoor.es/index.htm')
        time.sleep(10)
        selenium.sendKeys('#inlineUserEmail', USER_EMAIL)
        sleep(2, 5)
        selenium.waitAndClick('.emailButton button[type=submit]')
        sleep(2, 5)
        selenium.waitUntilPageIsLoaded()
        sleep(1, 2)
        # 'login password slider wait'
        selenium.waitUntilClickable(CSS_SEL_PASSWORD_SUBMIT)
        selenium.waitUntil_presenceLocatedElement(CSS_SEL_PASSWORD_SUBMIT)
        selenium.waitUntil_presenceLocatedElement(CSS_SEL_INPUT_PASS)
        selenium.sendKeys(CSS_SEL_INPUT_PASS, USER_PWD)
        sleep(1, 2)
        selenium.waitAndClick(CSS_SEL_PASSWORD_SUBMIT)
        print(yellow('Waiting for Glassdoor to redirect after login...'))
        selenium.waitUntilPageUrlContains(
            'https://www.glassdoor.es/Empleo/index.htm', 60)
    except Exception as ex:
        debug(red(traceback.format_exc()))
        raise ex


@retry()
def getTotalResultsFromHeader(keywords: str) -> int:
    total = selenium.getText(CSS_SEL_SEARCH_RESULT_TOTAL).split(' ')[0]
    printHR(green)
    print(green(f'{total} total results for search: {keywords}'))
    printHR(green)
    return int(total)


def summarize(keywords, totalResults, currentItem):
    printHR()
    print(f'Loaded {currentItem} of {totalResults} total results for',
          f'search: {keywords}')
    printHR()
    print()


@retry(exception=NoSuchElementException)
def clickNextPage():
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
    selenium.waitUntilPageIsLoaded()


def getJobId(url: str):
    # https://www.glassdoor.es/job-listing/telecom-support-engineer-skyvera-remote-60-000-year-usd-crossover-JV_IC2547194_KO0,55_KE56,65.htm?jl=1009552660667&src=GD_JOB_AD&ao=1110586&jrtk=5-yul1-0-1ieb5v41mi8oh800-e71236e165c7d622---6NYlbfkN0Bp-pWyh_yd7-BMq_HjiKF8q-wDEEHI6K3EhZcTze0zEjIHj4r45OmtWfbbiAi_eIZuGypcbT_DdfyeGTzRrDYphDn3IzgUnq8LYdoPPjlTQRT7F5LIfGITPRrOGm_f1RqD5UM3Uud4MFzXJ0DAYia8heQWKVQTbEUgq9yaVeGvQEaaB9voulayu49wH_siPfiHxLoeEkzwKGWtpAV0LQU0XvSZOP_3bnp9H01zvitX4HCGh_n8z84Q2LPuFKsEHTPZlhhTkTE1eSktmj6vNHhNzs1PGmPPeddnlkD5qw86Z8NFLaOT9ldFBD0i0nnPq5MHYnPlN2BiXMNuwD5FfohRQxxrB1s958tWneiFNf_PtEdxoXxMs2y5mcGMuZ3frX-xhCyyBYj2I8s63MDQg3Js6vGblTIJABNBgPGz1Q8Ei6TmNtA0biVVJTVBs8xM_v6MkBAEltu2ipF711OETqz7MqXegWOupKJKZZ_kWmBC6xyJ8L6bmtjWKaAnlJVw2oyLk1G5QNW3COWK1emQjQkcHLYI3W95K2dx3NBdXZWnlDXfT-AAoF48DydZuzBkTsorWnH7nVC85ebAQQ6h1CH1iHbAaYry6pHrUxRB3DLYWj8hL2B-T1ece1PjXMYzu7KZP91F1tXO4NQk98G2iaKEv_E30vhWJUKWxdQBdGI-d7RJsxMOXLzH-QKkp2zU4BZWTJsifiKz0fO7v97xznnelhX4Nb2yDF7OSWUXtnhnFj-mNRCHos7wasN4GLRz0WxMSqsAuUsTHiS_UwrkFYp79u09ZJz5h9Mkrlp6xN35kR_LOByEfzoXcmM_M0os3W6eBkSS7Rw4abuB4xGmDl0ckNq0ohQTtavsHUKFdYwI8wcpBUuVrL8BhFQUL3-r969GkYJ7bzKwHVYCSnfa9K6Q5UfPx2NkhF0%253D&cs=1_5bbdeada&s=58&t=SR&pos=102&cpc=2CAED5C921A5F994&guid=00000193965f8ff984666794c6547271&jobListingId=1009552660667&ea=1&vt=w&cb=1733394665730&ctt=1733394906726
    return re.sub(r'.*[?&](jl|jobListingId)=([0-9]+).*', r'\2',
                  url, flags=re.I)


def reInitSeleniumAndLogin():
    global selenium
    # Cloudflare filter retrying with new selenium driver
    debug(yellow("Reinitializing selenium"))
    selenium.close()
    selenium = SeleniumUtil()
    login()


@retry(exceptionFnc=reInitSeleniumAndLogin)
def searchJobs(url: str):
    keywords = url.split('/')
    keywords = keywords[len(keywords)-1:]
    print(yellow(f'Loading page {url}'))
    selenium.loadPage(url)
    selenium.waitUntilPageIsLoaded()
    print(yellow('Wait for page to load...'))
    sleep(8, 10)
    totalResults = getTotalResultsFromHeader(keywords)
    if totalResults > 0:
        sleep(1, 2)
        selenium.waitAndClick_noError(
            CSS_SEL_DIALOG_CLOSE, 'Could not close dialog', False)
        sleep(1, 2)
        selenium.waitAndClick_noError(
            CSS_SEL_COOKIES_ACCEPT,
            'Could not click accept cookies', False)
        sleep(1, 2)
        totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        page = 0
        currentItem = 0
        while currentItem < totalResults:
            page += 1
            printPage(WEB_PAGE, page, totalPages, keywords)
            idx = 0
            while idx < JOBS_X_PAGE and currentItem < totalResults:
                print(green(f'pg {page} job {idx + 1} - '), end='')
                loadAndProcessRow(idx)
                currentItem += 1
                idx += 1
            if currentItem < totalResults:
                clickNextPage()
        summarize(keywords, totalResults, currentItem)


@retry()
def loadAndProcessRow(idx):
    allLis = selenium.getElms(CSS_SEL_JOB_LI)
    liElm = allLis[idx]
    scrollJobsList(idx, liElm)
    jobId, jobExists = jobExistsInDB(liElm)
    if not jobExists:
        loadJobDetail(liElm)
    if jobExists:
        print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
    else:
        try:
            sleep(0.5, 1.5)
            processRow()
        finally:
            sleep(0.5, 1.5)
            selenium.back()
    return


@retry()
def scrollJobsList(idx, liElm):
    if idx < 3:
        return
    if idx < JOBS_X_PAGE-3:  # scroll to job link
        # in last page could not exist
        sleep(1, 2)
        selenium.scrollIntoView_noError(liElm)


def jobExistsInDB(liElm):
    url = selenium.getAttrOf(liElm, LI_JOB_TITLE_CSS_SUFFIX, 'href')
    jobId = getJobId(url)
    return (jobId, mysql.getJob(jobId) is not None)


def loadJobDetail(liElm):
    print(yellow('loading... '), end='')
    href = selenium.getAttrOf(liElm, LI_JOB_TITLE_CSS_SUFFIX, 'href')
    selenium.loadPage(href)


@retry()
def processRow():
    title = selenium.getText(CSS_SEL_JOB_TITLE)
    company = selenium.getElms(CSS_SEL_COMPANY)
    if len(company) == 1:
        company = company[0].text
    else:
        company = selenium.getText(CSS_SEL_COMPANY2)
    location = selenium.getText(CSS_SEL_LOCATION)
    selenium.waitUntilClickable(CSS_SEL_JOB_TITLE)
    url = selenium.getUrl()
    jobId = getJobId(url)
    html = selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
    md = htmlToMarkdown(html)
    # easyApply: there are 2 buttons
    easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
    print(f'{jobId}, {title}, {company}, {location}, ',
          f'easy_apply={easyApply} - ', end='')
    if validate(title, url, company, md, DEBUG):
        if mysql.insert((jobId, title, company, location, url, md,
                        easyApply, WEB_PAGE)):
            print(green('INSERTED!'), end='')
    else:
        raise ValueError('Validation failed')
    print()


def debug(msg: str = ''):
    baseScrapper.debug(DEBUG, msg)
