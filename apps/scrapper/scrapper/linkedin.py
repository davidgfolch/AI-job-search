import math
from selenium.common.exceptions import NoSuchElementException

from .core import baseScrapper
from .core.baseScrapper import getAndCheckEnvVars, printScrapperTitle
from commonlib.terminalColor import yellow, green
from commonlib.mysqlUtil import MysqlUtil
from .services.selenium.seleniumService import SeleniumService
from .util.persistence_manager import PersistenceManager
from .navigator.linkedinNavigator import LinkedinNavigator
from .services.LinkedinService import LinkedinService

USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("LINKEDIN")

remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
# Spain if you need other make a manual search and get your country code
location = '105646813'
f_TPR = 'r86400'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = True

WEB_PAGE = 'Linkedin'
JOBS_X_PAGE = 25

print('Linkedin scrapper init')
navigator: LinkedinNavigator = None
service: LinkedinService = None

def run(seleniumUtil: SeleniumService, preloadPage: bool, persistenceManager: PersistenceManager):
    """Login, process jobs in search paginated list results"""
    global navigator, service
    navigator = LinkedinNavigator(seleniumUtil)
    printScrapperTitle('LinkedIn', preloadPage)
    if preloadPage:
        navigator.login(USER_EMAIL, USER_PWD)
        print(yellow('Waiting for LinkedIn to redirect to feed page... (Maybe you need to solve a security filter first)'))
        navigator.wait_until_page_url_contains('https://www.linkedin.com/feed/', 60)
        return
    with MysqlUtil() as mysql:
        service = LinkedinService(mysql, persistenceManager)
        service.set_debug(DEBUG)
        service.prepare_resume()
        for keywords in JOBS_SEARCH.split(','):
            keyword = keywords.strip()
            skip, start_page = service.should_skip_keyword(keyword)
            if skip:
                print(yellow(f"Skipping keyword '{keyword}' (already processed)"))
                continue
            try:
                process_keyword(keyword, start_page)
            except Exception:
                baseScrapper.debug(DEBUG)
    service.clear_state()

def process_keyword(keyword: str, start_page: int):
    url = load_page(keyword)
    if navigator.check_login_popup(lambda: navigator.login(USER_EMAIL, USER_PWD)):
        url = load_page(keyword)
    if navigator.check_results(keyword, url, remote, location, f_TPR):
        search_jobs(keyword, start_page)

def load_page(keywords: str) -> str:
    from urllib.parse import quote
    print(yellow(f'Search keyword={keywords}'))
    url = f'https://www.linkedin.com/jobs/search/?keywords={quote(keywords)}&f_WT={remote}&geoId={location}&f_TPR={f_TPR}'
    navigator.load_page(url)
    return url

def search_jobs(keywords: str, startPage: int):
    try:
        navigator.collapse_messages()
        totalResults = navigator.get_total_results(keywords, remote, location, f_TPR)
        totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        currentItem = 0
        page = _fast_forward_page(startPage, currentItem, totalResults)
        while True:
            foundNewJobInPage = False
            baseScrapper.printPage(WEB_PAGE, page, totalPages, keywords)
            rowErrors = 0
            for idx in range(1, JOBS_X_PAGE+1):
                if currentItem >= totalResults:
                    break
                currentItem += 1
                print(green(f'pg {page} job {idx} - '), end='', flush=True)
                jobExistsInDb = load_and_process_row(idx, rowErrors)
                if rowErrors > 1:
                    break
                if not jobExistsInDb:
                    foundNewJobInPage = True
            if currentItem >= totalResults or page >= totalPages:
                break
            if not foundNewJobInPage and page==1:
                print(yellow('No new jobs found in this page, stopping keyword processing.'))
                break
            if not navigator.click_next_page():
                break
            page += 1
            navigator.wait_until_page_is_loaded()
            service.update_state(keywords, page)
        summarize(keywords, totalResults, currentItem)
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)

def _fast_forward_page(startPage: int, currentItem: int, totalResults: int):
    page = 1
    if startPage > 1:
        print(yellow(f"Fast forwarding to page {startPage}..."))
        while page < startPage:
            currentItem += JOBS_X_PAGE 
            if navigator.click_next_page():
                page += 1
                navigator.wait_until_page_is_loaded()
            else:
                break
        currentItem = (page - 1) * JOBS_X_PAGE
    return page

def load_and_process_row(idx, rowErrors):
    try:
        cssSel = navigator.scroll_jobs_list(idx)
        url = navigator.get_job_url_from_element(cssSel)
        jobId, jobExists = service.job_exists_in_db(url)
        navigator.load_job_detail(jobExists, idx, cssSel)
        if jobExists:
            print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
            return True
        process_row(idx)
        print()
        return False
    except NoSuchElementException:
        baseScrapper.debug(DEBUG, "NoSuchElement in loadAndProcessRow ", exception=True)
        print()
        rowErrors += 1
        return False

def process_row(idx):
    isDirectUrlScrapping = idx is None
    try:
        if isDirectUrlScrapping:
            title, company, location, url, html = navigator.getJobInList_directUrl()
        else:
            title, company, location, url, html = navigator.getJobInList(idx)
        easyApply = navigator.check_easy_apply()
        service.process_job(title, company, location, url, html, isDirectUrlScrapping, easyApply)
    except (ValueError, KeyboardInterrupt) as e:
        raise e
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)
        raise

def _transform_to_search_url(url: str) -> str:
    import re
    # helper logic to transform standard job url to search url (which has same structure as the one used in the list)
    # https://www.linkedin.com/jobs/view/4350893693/ -> https://www.linkedin.com/jobs/search/?currentJobId=4350893693
    match = re.search(r'linkedin.com/jobs/view/(\d+)', url)
    if match:
        jobId = match.group(1)
        url = f'https://www.linkedin.com/jobs/search/?currentJobId={jobId}'
    return url

def processUrl(url: str):
    global navigator, service
    url = _transform_to_search_url(url)
    with MysqlUtil() as mysql, SeleniumService() as seleniumUtil:
        navigator = LinkedinNavigator(seleniumUtil)
        service = LinkedinService(mysql, PersistenceManager())
        service.set_debug(DEBUG)
        navigator.load_page(url)
        if navigator.check_login_popup(lambda: navigator.login(USER_EMAIL, USER_PWD)):
            navigator.load_page(url)
        process_row(None)

def summarize(keywords, totalResults, currentItem):
    from commonlib.terminalColor import printHR
    from commonlib.util import getDatetimeNowStr
    printHR()
    print(f'{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords}',
          f'(remote={remote} location={location} last={f_TPR})')
    printHR()
    print()
