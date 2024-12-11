import math
import time
from urllib.parse import quote
import re
from selenium.common.exceptions import NoSuchElementException
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import htmlToMarkdown, join, validate
from ai_job_search.scrapper.util import getAndCheckEnvVars
from ai_job_search.tools.terminalColor import green, red, yellow
from .seleniumUtil import SeleniumUtil
from ai_job_search.tools.mysqlUtil import MysqlUtil
from ai_job_search.scrapper.selectors.glassdoorSelectors import (
    CSS_SEL_COOKIES_ACCEPT,
    CSS_SEL_JOB_DESCRIPTION,
    CSS_SEL_JOB_EASY_APPLY,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND,
    CSS_SEL_JOB_LI_IDX,
    CSS_SEL_COMPANY,
    CSS_SEL_LOCATION,
    LI_JOB_TITLE_CSS_SUFFIX,
    CSS_SEL_JOB_LINK)


USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("GLASSDOOR")
remote = 1
fromAge = 1
country = 'españa'

DEBUG = True

JOBS_X_PAGE = 25  # TODO: NOT KNOWN YET HOW WORKS PAGINATION

print('seleniumGlassdoor init')
selenium = None
mysql = None


def run(seleniumUtil: SeleniumUtil):
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    selenium = seleniumUtil
    try:
        mysql = MysqlUtil()
        login()
        print(yellow('Waiting for Glassdoor to redirect after login...'))
        selenium.waitUntilPageUrlContains(
            'https://www.glassdoor.es/Empleo/index.htm', 60)
        for url in JOBS_SEARCH.split('\n'):
            searchJobs(url)
    finally:
        mysql.close()


def login():
    try:
        selenium.loadPage('https://www.glassdoor.es/index.htm')
        selenium.sendKeys('#inlineUserEmail', USER_EMAIL)
        selenium.waitAndClick('.emailButton > button[type=submit]')
        print('waitUntilPageIsLoaded')
        selenium.waitUntilPageIsLoaded()
        time.sleep(1)
        CSS_SEL_PASSWORD_SUBMIT = 'form button[type=submit]'
        # 'login password slider wait'
        print('waitUntilClickable(CSS_SEL_PASSWORD_SUBMIT)')
        selenium.waitUntilClickable(CSS_SEL_PASSWORD_SUBMIT)
        print('waitUntil_presenceLocatedElement(CSS_SEL_PASSWORD_SUBMIT)')
        selenium.waitUntil_presenceLocatedElement(CSS_SEL_PASSWORD_SUBMIT)
        print('waitUntil_presenceLocatedElement(CSS_SEL_PASSWORD_SUBMIT)')
        CSS_SEL_INPUT_PASS = 'form input#inlineUserPassword'
        selenium.waitUntil_presenceLocatedElement(CSS_SEL_INPUT_PASS)
        # print("""selenium.waitUntilFoundMany(
        #     CSS_SEL_INPUT_PASS, 1, 'wait until #inlineUserPassword')""")
        # selenium.waitUntilFoundMany(
        #     CSS_SEL_INPUT_PASS, 1, 'wait until #inlineUserPassword')
        # selenium.waitUntilClickable('#inlineUserPassword')
        print('sendKeys to pass')
        selenium.sendKeys(CSS_SEL_INPUT_PASS, USER_PWD)
        selenium.waitAndClick(CSS_SEL_PASSWORD_SUBMIT)
    except Exception as ex:
        debug(red(f'ERROR: {ex}'))
        raise ex


def getUrl(keywords):
    # TODO: what is SRCH_IL.0,9_IC2547194_KO10,14 in url
    return join(
        f'https://www.glassdoor.es/Empleo/{country}-{quote(keywords)}-empleos',
        '-SRCH_IL.0,9_IC2547194_KO10,14.htm?',
        f'remoteWorkType={remote}&fromAge={fromAge}&sortBy=date_desc')


def checkResults(keywords: str, url: str):
    # noResultElm = selenium.getElms(CSS_SEL_NO_RESULTS)
    # if len(noResultElm) > 0:
    #     print(Exception(
    #         join('No results for job search on Glassdoor for',
    #              f'keywords={keywords}', f'remote={remote}',
    #              f'URL {url}')))
    #     debug(f'checkResults -> no results for search={keywords}')
    #     return False
    return True


def replaceIndex(idx: int):
    return CSS_SEL_JOB_LI_IDX.replace('##idx##', str(idx))


def getTotalResultsFromHeader(keywords: str) -> int:
    total = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
    print(green('-'*150))
    print(green(join(f'{total} total results for search: {keywords}',
                     f'(remote={remote}, fromAge={fromAge})')))
    print(green('-'*150))
    return int(total)


def summarize(keywords, totalResults, currentItem):
    print('-'*150)
    print(f'Loaded {currentItem} of {totalResults} total results for',
          f'search: {keywords}',
          f'(remote={remote} fromAge={fromAge})')
    print('-'*150)
    print()


def printPage(page, totalPages, keywords):
    print(green(f'Starting page {page} of {totalPages} ',
                f'search={keywords} {"-"*100}'))


def clickNextPage(retry=True):
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    # TODO: HOW TO NEXT PAGE
    return False
    # try:
    #     selenium.waitAndClick(
    #         CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
    #     return True
    # except NoSuchElementException:
    #     if retry:
    #         debug("retry clickNextPage")
    #         clickNextPage(False)
    #     return False


def getJobId(url: str):
    # https://www.glassdoor.es/job-listing/telecom-support-engineer-skyvera-remote-60-000-year-usd-crossover-JV_IC2547194_KO0,55_KE56,65.htm?jl=1009552660667&src=GD_JOB_AD&ao=1110586&jrtk=5-yul1-0-1ieb5v41mi8oh800-e71236e165c7d622---6NYlbfkN0Bp-pWyh_yd7-BMq_HjiKF8q-wDEEHI6K3EhZcTze0zEjIHj4r45OmtWfbbiAi_eIZuGypcbT_DdfyeGTzRrDYphDn3IzgUnq8LYdoPPjlTQRT7F5LIfGITPRrOGm_f1RqD5UM3Uud4MFzXJ0DAYia8heQWKVQTbEUgq9yaVeGvQEaaB9voulayu49wH_siPfiHxLoeEkzwKGWtpAV0LQU0XvSZOP_3bnp9H01zvitX4HCGh_n8z84Q2LPuFKsEHTPZlhhTkTE1eSktmj6vNHhNzs1PGmPPeddnlkD5qw86Z8NFLaOT9ldFBD0i0nnPq5MHYnPlN2BiXMNuwD5FfohRQxxrB1s958tWneiFNf_PtEdxoXxMs2y5mcGMuZ3frX-xhCyyBYj2I8s63MDQg3Js6vGblTIJABNBgPGz1Q8Ei6TmNtA0biVVJTVBs8xM_v6MkBAEltu2ipF711OETqz7MqXegWOupKJKZZ_kWmBC6xyJ8L6bmtjWKaAnlJVw2oyLk1G5QNW3COWK1emQjQkcHLYI3W95K2dx3NBdXZWnlDXfT-AAoF48DydZuzBkTsorWnH7nVC85ebAQQ6h1CH1iHbAaYry6pHrUxRB3DLYWj8hL2B-T1ece1PjXMYzu7KZP91F1tXO4NQk98G2iaKEv_E30vhWJUKWxdQBdGI-d7RJsxMOXLzH-QKkp2zU4BZWTJsifiKz0fO7v97xznnelhX4Nb2yDF7OSWUXtnhnFj-mNRCHos7wasN4GLRz0WxMSqsAuUsTHiS_UwrkFYp79u09ZJz5h9Mkrlp6xN35kR_LOByEfzoXcmM_M0os3W6eBkSS7Rw4abuB4xGmDl0ckNq0ohQTtavsHUKFdYwI8wcpBUuVrL8BhFQUL3-r969GkYJ7bzKwHVYCSnfa9K6Q5UfPx2NkhF0%253D&cs=1_5bbdeada&s=58&t=SR&pos=102&cpc=2CAED5C921A5F994&guid=00000193965f8ff984666794c6547271&jobListingId=1009552660667&ea=1&vt=w&cb=1733394665730&ctt=1733394906726
    return re.sub(r'.*[?&](jl|jobListingId)=([0-9]+).*', r'\2',
                  url, flags=re.I)


def searchJobs(url: str):
    # try:
    keywords = url.split('/')
    keywords = keywords[len(keywords)-1:]
    selenium.loadPage(url)
    selenium.waitUntilPageIsLoaded()
    # if not checkResults(keywords, url):
    #     return
    selenium.waitAndClick_noError('div[data-test="Modal-content"] button[data-test=job-alert-modal-close]',
                                  'Could not close dialog')
    selenium.waitAndClick_noError(CSS_SEL_COOKIES_ACCEPT,
                                  'Could not click accept cookies')
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
    # except Exception as ex:
    #     debug(red(f'ERROR: {ex}'))


def loadAndProcessRow(idx, retry=True):
    try:
        scrollJobsList(idx)
        jobId, jobExists = jobExistsInDB(idx)
        if not jobExists:
            loadJobDetail(idx)
    except Exception as ex:
        debug("NoSuchElement in loadAndProcessRow " +
              red(f'ERROR: {ex}'))
        print(ex)
        if retry:
            time.sleep(5)
            loadAndProcessRow(idx, False)
            return
        else:
            raise ex
    if jobExists:
        print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
    else:
        # tryFnc(processRow, 'processRow', idx)
        processRow(idx)


def scrollJobsList(idx):
    if idx < 3:
        return
    if idx < JOBS_X_PAGE-3:  # scroll to job link
        cssSel = replaceIndex(idx - 1)
        # in last page could not exist
        if not selenium.scrollIntoView_noError(cssSel):
            print(yellow(' waiting 10 secs... & retrying... '))
            time.sleep(5)
            selenium.scrollIntoView_noError(cssSel)


def jobExistsInDB(idx):
    cssSel = replaceIndex(idx)
    cssSel = f'{cssSel} {CSS_SEL_JOB_LINK}'
    url = selenium.getAttr(cssSel, 'href')
    jobId = getJobId(url)
    return (jobId, mysql.getJob(jobId) is not None)


def loadJobDetail(idx: int):
    # first job in page loads automatically
    # if job exists in DB no need to load details (rate limit)
    if idx == 1:
        return
    cssSel = replaceIndex(idx)
    cssSel = f'{cssSel} {CSS_SEL_JOB_LINK}'
    # selenium.waitUntilClickable(cssSel)
    print(yellow('loading... '), cssSel, end='')
    selenium.waitAndClick(cssSel)  # FIXME: SOMETIMES DOESNT WORK


def processRow(idx, retry=True):
    # TODO: CSS_SEL_JOB_CLOSED -> No longer accepting applications
    # https://www.glassdoor.com/jobs/view/4057715315/
    # TODO: AI -> Language ignore (german f.ex.)
    # try:
    liPrefix = replaceIndex(idx)
    print(f'title css -> {liPrefix} {LI_JOB_TITLE_CSS_SUFFIX}')
    title = selenium.getText(f'{liPrefix} {LI_JOB_TITLE_CSS_SUFFIX}')
    print(f'company css -> {liPrefix} {CSS_SEL_COMPANY}')
    company = selenium.getText(f'{liPrefix} {CSS_SEL_COMPANY}')
    location = selenium.getText(f'{liPrefix} {CSS_SEL_LOCATION}')
    cssSelLink = f'{liPrefix} {CSS_SEL_JOB_LINK}'
    selenium.waitUntilClickable(cssSelLink)
    url = selenium.getAttr(cssSelLink, 'href')
    # url = getJobUrlShort(selenium.getAttr(CSS_SEL_JOB_LINK, 'href'))
    print(f'url -> {url}')
    jobId = getJobId(url)
    print(f'jobId -> {jobId}')
    html = selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
    print(f'html -> {html}')
    md = htmlToMarkdown(html)
    print(f'markdown -> {md}')
    # easyApply: there are 2 buttons
    easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
    print(f'{jobId}, {title}, {company}, {location}, ',
          f'easy_apply={easyApply} - ', end='')
    if validate(title, url, company, md, DEBUG):
        if mysql.insert((jobId, title, company, location, url, md,
                         easyApply, 'Glassdoor')):
            print(green('INSERTED!'), end='')
    elif retry:
        print(yellow('waiting 10 secs... & retrying... '))
        time.sleep(10)
        processRow(idx, retry=False)
        return
    # except Exception as ex:
    #     debug('processRow Exception -> ' + red(f'ERROR: {ex}'))
    print()


def tryFnc(fnc, errMessage: str, *params):
    try:
        fnc(*params)
    except Exception as ex:
        debug(f'{errMessage} Exception -> ' + red(f'ERROR: {ex}'))
        if DEBUG:
            raise ex


def debug(msg: str = ''):
    baseScrapper.debug(DEBUG, msg)
