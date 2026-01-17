import math
from commonlib.terminalColor import green, yellow
from commonlib.mysqlUtil import MysqlUtil
from .core import baseScrapper
from .core.baseScrapper import getAndCheckEnvVars, printScrapperTitle
from .services.selenium.seleniumService import SeleniumService
from .util.persistence_manager import PersistenceManager
from .navigator.infojobsNavigator import InfojobsNavigator
from .services.InfojobsService import InfojobsService

USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("INFOJOBS")

DEBUG = True
WEB_PAGE = 'Infojobs'
LIST_URL = 'https://www.infojobs.net/ofertas-trabajo'
JOBS_X_PAGE = 22

print('Infojobs scrapper init')
navigator: InfojobsNavigator = None
service: InfojobsService = None

def run(seleniumUtil: SeleniumService, preloadPage: bool, persistenceManager: PersistenceManager):
    """Process jobs in search paginated list results"""
    global navigator, service
    navigator = InfojobsNavigator(seleniumUtil)
    printScrapperTitle('Infojobs', preloadPage)
    if preloadPage:
        # For preloading, we can just use the navigator logic
        navigator.load_search_page()
        if not seleniumUtil.driverUtil.useUndetected:
            navigator.security_filter()
        return
    with MysqlUtil() as mysql:
        service = InfojobsService(mysql, persistenceManager)
        service.set_debug(DEBUG)
        service.prepare_resume()
        for keywords in JOBS_SEARCH.split(','):
            current_keyword = keywords.strip()
            skip, start_page = service.should_skip_keyword(current_keyword)
            if skip:
                print(yellow(f"Skipping keyword '{current_keyword}' (already processed)"))
                continue
            try:
                process_keyword(current_keyword, start_page)
                persistenceManager.remove_failed_keyword(WEB_PAGE, current_keyword)
            except Exception:
                baseScrapper.debug(DEBUG)
                persistenceManager.add_failed_keyword(WEB_PAGE, current_keyword)
    persistenceManager.finalize_scrapper(WEB_PAGE)

def process_keyword(keywords: str, start_page: int):
    print(yellow(f'Search keyword={keywords}'))
    navigator.load_search_page()
    if not navigator.load_filtered_search_results(keywords):
        return
    totalResults = navigator.get_total_results_from_header(keywords)
    totalPages = math.ceil(totalResults / JOBS_X_PAGE)
    page = baseScrapper.fast_forward_page(navigator, start_page, totalResults, JOBS_X_PAGE)
    currentItem = (page - 1) * JOBS_X_PAGE
    while currentItem < totalResults:
        foundNewJobInPage = False
        baseScrapper.printPage(WEB_PAGE, page, totalPages, keywords)
        idx = 0
        while idx < JOBS_X_PAGE and currentItem < totalResults:
            print(green(f'pg {page} job {idx+1} - '), end='', flush=True)
            jobExistsInDb = load_and_process_row(idx)
            if not jobExistsInDb:
                foundNewJobInPage = True
            currentItem += 1
            idx += 1
        if not foundNewJobInPage and (page > start_page + 1 or (start_page<2 and page > 2)):
            print(yellow('No new jobs found in this page, stopping keyword processing.'))
            break
        if currentItem < totalResults:
            if navigator.click_next_page():
                page += 1
                navigator.wait_until_page_is_loaded()
                service.update_state(keywords, page)
            else:
                break
    baseScrapper.summarize(keywords, totalResults, currentItem)


def load_and_process_row(idx) -> bool:
    try:
        if idx > 2:
            try:
                navigator.scroll_jobs_list(idx)
            except Exception:
                print(yellow(f'Could not scroll to link {idx+1}, IGNORING.'), end='')
                return False
        job_link_elm = navigator.get_job_link_element(idx)
        url = navigator.get_job_url(job_link_elm)
        job_id, job_exists = service.job_exists_in_db(url)
        if job_exists:
            print(yellow(f'Job id={job_id} already exists in DB, IGNORED.'), end='', flush=True)
            return True
        print(yellow('loading...'), end='')

        navigator.click_job_link(job_link_elm)
        if not process_row(url):
             raise ValueError('Validation failed')
    except Exception:
        baseScrapper.debug(DEBUG, exception=True)
        return False
    finally:
        print(flush=True)
        if LIST_URL not in navigator.get_url():
            navigator.go_back()
    return False


def process_row(url):
    try:
        title, company, location, html = navigator.get_job_data()
        return service.process_job(title, company, location, url, html)
    except Exception as e:
        baseScrapper.debug(DEBUG, exception=True)
        raise e
