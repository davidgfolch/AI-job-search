import math
import traceback
from urllib.parse import quote
from selenium.common.exceptions import NoSuchElementException
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.baseScrapper import (
    getAndCheckEnvVars, htmlToMarkdown, join, printPage,
    printScrapperTitle, validate)
from ai_job_search.tools.terminalColor import (
    green, printHR, yellow)
from ai_job_search.tools.decorator.retry import retry
from ai_job_search.viewer.clean.mergeDuplicates import (
    getSelect, mergeDuplicatedJobs)
from .seleniumUtil import SeleniumUtil, sleep
from ai_job_search.tools.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from .selectors.tecnoempleoSelectors import (
    CSS_SEL_JOB_DATA,
    CSS_SEL_JOB_DESCRIPTION,
    CSS_SEL_JOB_LI_IDX,
    CSS_SEL_NO_RESULTS,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND,
    CSS_SEL_JOB_LI_IDX_LINK,
    CSS_SEL_COMPANY,
    CSS_SEL_JOB_TITLE,
    CSS_SEL_PAGINATION_LINKS)


USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("TECNOEMPLEO")

remote = ',1,'
las24Hours = '1'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False

WEB_PAGE = 'Tecnoempleo'
JOBS_X_PAGE = 30

print('Tecnoempleo scrapper init')
selenium = None
mysql = None


def run():
    """Login, process jobs in search paginated list results"""
    global selenium, mysql
    printScrapperTitle('Tecnoempleo')
    with MysqlUtil() as mysql, SeleniumUtil() as selenium:
        selenium.loadPage('https://www.tecnoempleo.com')
        selenium.waitUntilPageIsLoaded()
        login()
        print(yellow('Waiting for Tecnoempleo to redirect to jobs page...'))
        selenium.waitUntilPageUrlContains(
            'https://www.tecnoempleo.com/profesionales/candidat.php', 60)
        for keywords in JOBS_SEARCH.split(','):
            searchJobs(keywords.strip())


def login():
    # selenium.loadPage('https://www.tecnoempleo.com/demanda-trabajo-informatica.php')
    sleep(2, 2)
    selenium.waitAndClick('nav ul li a[title="Acceso Candidatos"]')
    selenium.waitUntilPageIsLoaded()
    cloudFlareSecurityFilter()
    selenium.sendKeys('#e_mail', USER_EMAIL)
    selenium.sendKeys('#password', USER_PWD)
    selenium.waitAndClick('form input[type=submit]')

@retry(retries=60, delay=5, exception=NoSuchElementException)
def cloudFlareSecurityFilter():
    print(yellow('SOLVE A SECURITY FILTER in selenium webbrowser...'), end='')
    sleep(4, 4)
    selenium.getElm('#e_mail')


def getUrl(keywords):
    return join('https://www.tecnoempleo.com/ofertas-trabajo/?',
                '&'.join([
                    f'te={quote(keywords)}',
                    f'en_remoto={remote}',
                    # f'ult_24h={las24Hours}'
                ]))


def checkResults(keywords: str, url: str):
    noResultElm = selenium.getElms(CSS_SEL_NO_RESULTS)
    if len(noResultElm) > 0:
        print(Exception(
            join('No results for job search on Tecnoempleo for',
                 f'keywords={keywords}', f'remote={remote}',
                 )))
        return False
    return True


def replaceIndex(cssSelector: str, idx: int):
    return cssSelector.replace('##idx##', str(idx))


def getTotalResultsFromHeader(keywords: str) -> int:
    total = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
    printHR(green)
    print(green(join(f'{total} total results for search: {keywords}',
                     f'(remote={remote})')))
    printHR(green)
    return int(total)


def summarize(keywords, totalResults, currentItem):
    printHR()
    print(f'Loaded {currentItem} of {totalResults} total results for',
          f'search: {keywords}',
          f'(remote={remote})')
    printHR()
    print()


def scrollJobsList(idx):
    cssSel = replaceIndex(CSS_SEL_JOB_LI_IDX, idx)
    # in last page could not exist
    scrollJobsListRetry(cssSel)
    cssSel = replaceIndex(CSS_SEL_JOB_LI_IDX_LINK, idx)
    selenium.waitUntilClickable(cssSel)
    return cssSel


def scrollToBottom():
    selenium.scrollIntoView('nav[aria-label=pagination]')


@retry(exceptionFnc=scrollToBottom)
def scrollJobsListRetry(cssSel):
    selenium.scrollIntoView(cssSel)


@retry(exception=NoSuchElementException, raiseException=False)
def clickNextPage():
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    nextPageElms = selenium.getElms(CSS_SEL_PAGINATION_LINKS)
    if len(nextPageElms) == 0:
        return False
    nextPageElm = nextPageElms[-1]
    if selenium.getText(nextPageElm).isnumeric():  # last link is not "next"
        return False
    selenium.waitAndClick(nextPageElm, scrollIntoView=True)
    return True


def jobExistsInDB(cssSel):
    url = selenium.getAttr(cssSel, 'href')
    jobId = getJobId(url)
    return (jobId, mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, jobId) is not None)


def getJobId(url: str):
    # https://www.tecnoempleo.com/integration-specialist-gstock-web-app/php-mysql-git-symfony-api-etl-sql-ja/rf-b14e1d3282dea3a42b40
    return url.split('/')[-1]


def acceptCookies():
    sleep(1,2)
    closeCreateAlert()
    cssSel = '#capa_cookie_rgpd > div.row > div:nth-child(1) > a'
    if len(selenium.getElms(cssSel)) > 0:
        selenium.waitAndClick(cssSel)


def closeCreateAlert():
    cssSel = '#wrapper_toast_br > div > div > button > span:nth-child(1)'
    if len(selenium.getElms(cssSel)) > 0:
        selenium.waitAndClick(cssSel)


def searchJobs(keywords: str):
    try:
        print(yellow(f'Search keyword={keywords}'))
        url = getUrl(keywords)
        print(yellow(f'Loading page {url}'))
        selenium.loadPage(url)
        selenium.waitUntilPageIsLoaded()
        if not checkResults(keywords, url):
            return
        acceptCookies()
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
                liIdx = 3+(idx-1)*2  # li starts at 3 & step 2
                ok = loadAndProcessRow(liIdx)
                # if page == 1:
                #     closeCreateAlert()
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
    except Exception:
        debug(traceback.format_exc())


def loadAndProcessRow(idx):
    pageLoaded = False
    try:
        cssSelLink = scrollJobsList(idx)
        jobId, jobExists = jobExistsInDB(cssSelLink)
        if jobExists:
            print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
            return True
        print(yellow('loading...'), end='')
        pageLoaded = loadDetail(cssSelLink)
        processRow()
    except Exception:
        debug(traceback.format_exc())
        return False
    finally:
        if pageLoaded:
            selenium.back()
    return True


@retry(raiseException=False)
def loadDetail(cssSelLink: str):
    selenium.waitAndClick(cssSelLink)
    return True


@retry()
def processRow():
    title = selenium.getText(CSS_SEL_JOB_TITLE)
    company = selenium.getText(CSS_SEL_COMPANY)
    location = ''
    url = selenium.getUrl()
    jobId = getJobId(url)
    html = '\n'.join(['- '+selenium.getText(elm)
                      for elm in selenium.getElms(CSS_SEL_JOB_DATA)]) + \
        '\n' * 2
    html += selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
    md = htmlToMarkdown(html)
    easyApply = False
    print(f'{jobId}, {title}, {company}, {location}, ',
          f'easy_apply={easyApply} - ', end='')
    if validate(title, url, company, md, DEBUG):
        if id := mysql.insert((jobId, title, company, location, url, md,
                               easyApply, WEB_PAGE)):
            print(green(f'INSERTED {id}!'), end='')
            mergeDuplicatedJobs(mysql.fetchAll(getSelect()))
    else:
        raise ValueError('Validation failed')
    print()


def debug(msg: str = ''):
    baseScrapper.debug(DEBUG, msg)
