import math
from selenium.common.exceptions import NoSuchElementException

from . import baseScrapper
from .baseScrapper import getAndCheckEnvVars, printScrapperTitle
from commonlib.terminalColor import yellow, green
from commonlib.mysqlUtil import MysqlUtil
from .seleniumUtil import SeleniumUtil
from .persistence_manager import PersistenceManager
from .selenium.linkedin_selenium import LinkedinNavigator
from .services.job_services.linkedin_job_service import LinkedinJobService

USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("LINKEDIN")

remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
# Spain if you need other make a manual search and get your country code
location = '105646813'
f_TPR = 'r86400'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False

WEB_PAGE = 'Linkedin'
JOBS_X_PAGE = 25

print('Linkedin scrapper init')
navigator: LinkedinNavigator = None
service: LinkedinJobService = None

def run(seleniumUtil: SeleniumUtil, preloadPage: bool, persistenceManager: PersistenceManager):
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
        service = LinkedinJobService(mysql, persistenceManager)
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
        page = 1
        currentItem = 0
        
        # Fast forward to startPage
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

        while True:
            baseScrapper.printPage(WEB_PAGE, page, totalPages, keywords)
            rowErrors = 0
            for idx in range(1, JOBS_X_PAGE+1):
                if currentItem >= totalResults:
                    break
                currentItem += 1
                print(green(f'pg {page} job {idx} - '), end='', flush=True)
                if not load_and_process_row(idx):
                    rowErrors += 1
                if rowErrors > 1:
                    break
            
            if currentItem >= totalResults or page >= totalPages or not navigator.click_next_page():
                break
            page += 1
            navigator.wait_until_page_is_loaded()
            service.update_state(keywords, page)
            
        summarize(keywords, totalResults, currentItem)
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)

def load_and_process_row(idx):
    try:
        cssSel = navigator.scroll_jobs_list(idx)
        url = navigator.get_job_url_from_element(cssSel)
        jobId, jobExists = service.job_exists_in_db(url)
        navigator.load_job_detail(jobExists, idx, cssSel)
        
        if jobExists:
            print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
            print()
            return True
        
        process_row(idx)
        print()
        return True
    except NoSuchElementException:
        baseScrapper.debug(DEBUG, "NoSuchElement in loadAndProcessRow ", exception=True)
        print()
        return False

def process_row(idx):
    isDirectUrlScrapping = idx is None
    try:
        if isDirectUrlScrapping:
            title, company, location, url, html = navigator.get_job_data_in_detail_page()
        else:
            title, company, location, url, html = navigator.get_job_data_in_list(idx)
            
        easyApply = navigator.check_easy_apply()
        service.process_job(title, company, location, url, html, isDirectUrlScrapping, easyApply)
    except (ValueError, KeyboardInterrupt) as e:
        raise e
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)
        raise

def processUrl(url: str):
    global navigator, service
    with MysqlUtil() as mysql, SeleniumUtil() as seleniumUtil:
        navigator = LinkedinNavigator(seleniumUtil)
        service = LinkedinJobService(mysql, PersistenceManager())
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
