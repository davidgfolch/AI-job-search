import math
from urllib.parse import quote
from commonlib.terminalColor import green, yellow
from commonlib.mysqlUtil import MysqlUtil
from commonlib.util import getDatetimeNowStr
from . import baseScrapper
from .baseScrapper import getAndCheckEnvVars, printScrapperTitle, join, printPage
from .seleniumUtil import SeleniumUtil
from .persistence_manager import PersistenceManager
from .selenium.tecnoempleo_selenium import TecnoempleoNavigator
from .services.job_services.tecnoempleo_job_service import TecnoempleoJobService

USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("TECNOEMPLEO")

remote = ',1,'
las24Hours = '1'  # last 24 hours
DEBUG = False
WEB_PAGE = 'Tecnoempleo'
JOBS_X_PAGE = 30

print('Tecnoempleo scrapper init')
navigator: TecnoempleoNavigator = None
service: TecnoempleoJobService = None

def run(seleniumUtil: SeleniumUtil, preloadPage: bool, persistenceManager: PersistenceManager):
    """Login, process jobs in search paginated list results"""
    global navigator, service
    navigator = TecnoempleoNavigator(seleniumUtil)
    
    printScrapperTitle('Tecnoempleo', preloadPage)
    
    if preloadPage:
        navigator.load_page('https://www.tecnoempleo.com')
        navigator.login(USER_EMAIL, USER_PWD)
        print(yellow('Waiting for Tecnoempleo to redirect to jobs page...'))
        navigator.wait_until_page_url_contains('https://www.tecnoempleo.com/profesionales/candidat.php', 60)
        return

    with MysqlUtil() as mysql:
        service = TecnoempleoJobService(mysql, persistenceManager)
        service.set_debug(DEBUG)
        service.prepare_resume()
        
        for keywords in JOBS_SEARCH.split(','):
            keyword = keywords.strip()
            
            should_skip, page = service.should_skip_keyword(keyword)
            if should_skip:
                print(yellow(f"Skipping keyword '{keyword}' (already processed)"))
                continue
                
            search_jobs(keyword, page)
            
    service.clear_state()

def get_url(keywords):
    return join('https://www.tecnoempleo.com/ofertas-trabajo/?',
                '&'.join([
                    f'te={quote(keywords)}',
                    f'en_remoto={remote}',
                    # f'ult_24h={las24Hours}'
                ]))

def search_jobs(keywords: str, start_page: int):
    try:
        print(yellow(f'Search keyword={keywords}'))
        url = get_url(keywords)
        print(yellow(f'Loading page {url}'))
        navigator.load_page(url)
        
        if not navigator.check_results(keywords, url, remote):
            return
            
        navigator.accept_cookies()
        totalResults = navigator.get_total_results_from_header(keywords, remote)
        totalPages = math.ceil(totalResults / JOBS_X_PAGE)
        page = 1
        currentItem = 0
        
        # Fast forward to startPage
        if start_page > 1:
            print(yellow(f"Fast forwarding to page {start_page}..."))
            while page < start_page:
                currentItem += JOBS_X_PAGE 
                if navigator.click_next_page():
                    page += 1
                    navigator.wait_until_page_is_loaded()
                else:
                    break
            currentItem = (page - 1) * JOBS_X_PAGE

        while True: # Pagination
            errors = 0
            printPage(WEB_PAGE, page, totalPages, keywords)
            for idx in range(1, JOBS_X_PAGE+1):
                if currentItem >= totalResults:
                    break  # exit for
                currentItem += 1
                print(green(f'pg {page} job {idx} - '), end='')
                liIdx = 3+(idx-1)*2  # li starts at 3 & step 2
                ok = load_and_process_row(liIdx)

                if not ok:
                    if navigator.check_rate_limit():
                        return False
                errors += 0 if ok else 1
                if errors > 1:  # exit page loop, some pages has less items
                    break
            
            if currentItem >= totalResults:
                break  # exit while
            if not navigator.click_next_page():
                break  # exit while
            page += 1
            navigator.wait_until_page_is_loaded()
            service.update_state(keywords, page)
            
        summarize(keywords, totalResults, currentItem)
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)

def load_and_process_row(idx):
    pageLoaded = False
    try:
        cssSelLink = navigator.scroll_jobs_list(idx)
        url = navigator.get_attribute(cssSelLink, 'href')
        
        job_id, job_exists = service.job_exists_in_db(url)
        
        if job_exists:
            print(yellow(f'Job id={job_id} already exists in DB, IGNORED.'), end='')
            return True
            
        print(yellow('loading...'), end='')
        pageLoaded = navigator.load_detail(cssSelLink)
        process_row()
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)
        return False
    finally:
        print(flush=True)
        if pageLoaded:
            navigator.go_back()
    return True

def process_row():
    title, company, location, url, html = navigator.get_job_data()
    return service.process_job(title, company, location, url, html)

def summarize(keywords, totalResults, currentItem):
    from commonlib.terminalColor import printHR
    printHR()
    print(f'{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords} (remote={remote})')
    printHR()
    print()