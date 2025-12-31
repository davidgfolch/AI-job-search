import math
from commonlib.terminalColor import green, yellow
from commonlib.mysqlUtil import MysqlUtil
from commonlib.util import getEnv
from .core import baseScrapper
from .core.baseScrapper import getAndCheckEnvVars, printScrapperTitle
from .services.selenium.seleniumService import SeleniumService
from .util.persistence_manager import PersistenceManager
from .navigator.glassdoorNavigator import GlassdoorNavigator
from .services.GlassdoorService import GlassdoorService

SITE = "GLASSDOOR"
USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars(SITE)
JOBS_SEARCH_BASE_URL = getEnv(f'{SITE}_JOBS_SEARCH_BASE_URL')

DEBUG = False
WEB_PAGE = 'Glassdoor'
JOBS_X_PAGE = 30

print('Glassdoor scrapper init')
navigator: GlassdoorNavigator = None
service: GlassdoorService = None

def run(seleniumUtil: SeleniumService, preloadPage: bool, persistenceManager: PersistenceManager):
    """Login, process jobs in search paginated list results"""
    global navigator, service
    navigator = GlassdoorNavigator(seleniumUtil)
    printScrapperTitle('Glassdoor', preloadPage)
    if preloadPage:
        navigator.load_main_page()
        return
    
    with MysqlUtil() as mysql:
        service = GlassdoorService(mysql, persistenceManager)
        service.set_debug(DEBUG)
        service.prepare_resume()
        for search in JOBS_SEARCH.split('|~|'):
            keyword = search
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
    url = JOBS_SEARCH_BASE_URL.format(**{'search': keyword})
    print(yellow(f'Search keyword={keyword}'))
    print(yellow(f'Loading page {url}'))
    navigator.load_page(url)
    navigator.wait_until_page_is_loaded()
    
    totalResults = navigator.get_total_results(keyword)
    if totalResults > 0:
        navigator.close_dialogs()
        totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        currentItem = 0
        page = _fast_forward_page(start_page, currentItem, totalResults)
        
        while currentItem < totalResults:
            baseScrapper.printPage(WEB_PAGE, page, totalPages, keyword)
            idx = 0
            while idx < JOBS_X_PAGE and currentItem < totalResults:
                print(green(f'pg {page} job {idx + 1} - '), end='', flush=True)
                load_and_process_row(idx)
                currentItem += 1
                idx += 1
            if currentItem < totalResults:
                if navigator.click_next_page():
                    page += 1
                    navigator.wait_until_page_is_loaded()
                    service.update_state(keyword, page)
                else:
                    break
        summarize(keyword, totalResults, currentItem)

def _fast_forward_page(start_page: int, current_item: int, total_results: int):
    page = 1
    if start_page > 1:
        print(yellow(f"Fast forwarding to page {start_page}..."))
        while page < start_page and current_item < total_results:
            if navigator.click_next_page():
                page += 1
                navigator.wait_until_page_is_loaded()
            else:
                break
        current_item = (page - 1) * JOBS_X_PAGE
    return page

def load_and_process_row(idx):
    try:
        all_lis = navigator.get_job_li_elements()
        if idx >= len(all_lis):
             return
        li_elm = all_lis[idx]
        navigator.scroll_jobs_list(idx, li_elm)
        
        url = navigator.get_job_url(li_elm)
        job_id, job_exists = service.job_exists_in_db(url)
        
        if job_exists:
            print(yellow(f'Job id={job_id} already exists in DB, IGNORED.'), end='')
        else:
            navigator.load_job_detail(li_elm)
            try:
                title, company, location, url, html, easy_apply = navigator.get_job_data()
                service.process_job(title, company, location, url, html, easy_apply)
            finally:
                navigator.go_back()
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)
    finally:
        print(flush=True)

def summarize(keywords, totalResults, currentItem):
    from commonlib.terminalColor import printHR
    from commonlib.util import getDatetimeNowStr
    printHR()
    print(f'{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords}')
    printHR()
    print()
