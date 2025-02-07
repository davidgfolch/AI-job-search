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
from ai_job_search.viewer.util.decorator.retry import retry
from .seleniumUtil import SeleniumUtil, sleep
from ai_job_search.tools.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
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
    CSS_SEL_NEXT_PAGE_BUTTON)


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
    # if idx < JOBS_X_PAGE-3:  # scroll to job link
    #     i = idx
    #     while i <= idx:
    # in last page could not exist
    debug("before scrollJobsList")
    li = selenium.getElms(CSS_SEL_JOB_LI)[idx]
    selenium.scrollIntoView_noError(li)
    sleep(0.5, 1)
    # i += 1
    debug("after scrollJobsList")


@retry(exception=NoSuchElementException, raiseException=False)
def clickNextPage():
    """Click on next to load next page.
    If there isn't next button in pagination we are in the last page,
    so return false to exit loop (stop processing)"""
    sleep(1, 2)
    selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
    return True


def loadJobDetail(jobLinkElm: WebElement):
    # first job in page loads automatically
    # if job exists in DB no need to load details (rate limit)
    print(yellow('loading...'), end='')
    sleep(2, 4)
    selenium.waitAndClick(jobLinkElm)
    sleep(9, 11)


def jobExistsInDB(url):
    jobId = getJobId(url)
    return (jobId, mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, jobId) is not None)


def getJobId(url: str):
    # https://es.indeed.com/pagead/clk?mo=r&ad=-6NYlbfkN0DbIyHopYNdPLgRYRG2FgnuJLz47mHLRnOVu2tY5XDnoTjm_t8c6thoU-53yYOVZJvZ76je_lq6KA-XAY92iGBEMkipCfXteoPVubXE4FHTfqx4Mf-6MhfZkK7YUu3yrI-z9JQE9pLO-djt1tFqNEtTK3NWMfyT0Ezmoj_8NOLQUumiyZsw8Hx3ykr2qLxPszYw1XYJLwKKdex1K0FkeMDl4M6poEhp9eoiIfvPBH-AGSl0J7kFrvnVDF5Cb6Dvrlcnad3Mvu-SvAvFBTP1OaSrIZMPkRPObPTtGFXsV0HO6KsqJx5bZwuzWhmu1B5dPhpGeEgMXWo0Cn3Bgc8D5VSbTCXIQDkq9i_5JDzpYeBo1uKtvyrS2lWXnCL9UNcz5eh8zDD8MU8-Pqk0vZPYzeaSWFWNqCidqZ9zcmNjFzMZdXdxTtOmr4lEs4GN__YlU0NBlGiq59uMCMRzFV93FcxbAC4oGzgFodV4uXx4dRB7zVAjTPLFlvNgsPUm6kHt7nDOe40xbCXB6STQc6axaa1tP1bRbfXH6sb6X8B_CK_kHRiPQ0omUdYa8RGGEtycz41lWTLwP1CT2zUOn64fuP3bIOeW9lPQFUW_Hi0n7r-KmA==&xkcb=SoCR6_M32Jfx9pTm350LbzkdCdPP&camk=nUmJqO2E8rjUsDRVvlAvpw==&p=0&fvj=0&vjs=3
    # https://es.indeed.com/pagead/clk?mo=r&ad=-6NYlbfkN0DbIyHopYNdPLgRYRG2FgnuJLz47mHLRnOVu2tY5XDnoTjm_t8c6thoU-53yYOVZJvZ76je_lq6KA-XAY92iGBEMkipCfXteoPVubXE4FHTfqx4Mf-6MhfZkK7YUu3yrI-z9JQE9pLO-djt1tFqNEtTK3NWMfyT0Ezmoj_8NOLQUumiyZsw8Hx3ykr2qLxPszYw1XYJLwKKdex1K0FkeMDl4M6poEhp9eoiIfvPBH-AGSl0J7kFrvnVDF5Cb6Dvrlcnad3Mvu-SvAvFBTP1OaSrIZMPkRPObPTtGFXsV0HO6KsqJx5bZwuzWhmu1B5dPhpGeEgMXWo0Cn3Bgc8D5VSbTCXIQDkq9i_5JDzpYeBo1uKtvyrS2lWXnCL9UNcz5eh8zDD8MU8-Pqk0vZPYzeaSWFWNqCidqZ9zcmNjFzMZdXdxTtOmr4lEs4GN__YlU0NBlGiq59uMCMRzFV93FcxbAC4oGzgFodV4uXx4dRB7zVAjTPLFlvNgsPUm6kHt7nDOe40xbCXB6STQc6axaa1tP1bRbfXH6sb6X8B_CK_kHRiPQ0omUdYa8RGGEtycz41lWTLwP1CT2zUOn64fuP3bIOeW9lPQFUW_Hi0n7r-KmA==&xkcb=SoCR6_M32Jfx9pTm350LbzkdCdPP&camk=nUmJqO2E8rjUsDRVvlAvpw==&p=0&fvj=0&vjs=3&tk=1ii9bvhamkhjt8e0&jsa=9049&oc=1&sal=0
    return re.sub(r'.+\?.*jk=([^&]+).*', r'\1', url)


def acceptCookies():
    selenium.waitAndClick_noError(
        '#onetrust-accept-btn-handler', 'Could not accept cookies')


def searchJobs(index: int, keywords: str):
    try:
        url = getUrl(keywords)
        selenium.loadPage(url)
        time.sleep(10)
        selenium.waitUntilPageIsLoaded()
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
                sleep(5, 6)
            else:
                break  # exit while
        summarize(keywords, totalResults, currentItem)
    except Exception:
        debug(exception=True)


def getJobLinkElement(idx):
    liElm = selenium.getElms(CSS_SEL_JOB_LI)[idx]
    return selenium.getElmOf(liElm, CSS_SEL_JOB_LINK)


@retry(raiseException=False)
def loadAndProcessRow(idx):
    ignore = True
    jobExists = False
    try:
        scrollJobsList(idx)
        jobLinkElm: WebElement = getJobLinkElement(idx)
        url = jobLinkElm.get_attribute('href')
        jobId, jobExists = jobExistsInDB(url)
        debug("after jobExistsInDB")
        # clean url just with jobId param
        url = f'https://es.indeed.com/viewjob?jk={jobId}'
        if jobExists:
            print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'),
                  end='')
            return True
        loadJobDetail(jobLinkElm)
        ignore = False
    except IndexError as ex:
        print(yellow("WARNING: could not get all items per page, that's ",
                     f"expected because not always has {JOBS_X_PAGE} pages: {ex}"))
    except Exception as ex:
        print(red(f'ERROR: {ex}'))
        debug(red(traceback.format_exc()))
    if not ignore:
        if not processRow(url):
            print(red('Validation failed'))
            return loadAndProcessRow(idx, False)
        selenium.back()
        sleep(1, 2)
        return True
    return False


@retry(raiseException=False)
def processRow(url):
    title = selenium.getText(CSS_SEL_JOB_TITLE).removesuffix('\n- job post')
    company = selenium.getText(CSS_SEL_COMPANY)
    # company = selenium.getText(CSS_SEL_COMPANY2)
    location = selenium.getText(CSS_SEL_LOCATION)
    jobId = getJobId(url)
    selenium.scrollIntoView(CSS_SEL_JOB_REQUIREMENTS)
    sleep(1, 2)
    selenium.waitUntil_presenceLocatedElement(CSS_SEL_JOB_REQUIREMENTS)
    html = selenium.getHtml(CSS_SEL_JOB_REQUIREMENTS)
    html += selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
    md = htmlToMarkdown(html)
    md = postProcessMarkdown(md)
    # easyApply: there are 2 buttons
    easyApply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
    print(f'{jobId}, {title}, {company}, {location}, {url}',
          f'easy_apply={easyApply} - ', end='')
    if validate(title, url, company, md, DEBUG):
        if mysql.insert((jobId, title, company, location, url, md,
                        easyApply, WEB_PAGE)):
            print(green('INSERTED!'), end='')
            return True
        else:
            debug(exception=True)
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
