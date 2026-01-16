import time
from commonlib.decorator.retry import retry
from commonlib.mysqlUtil import MysqlUtil
from .core import baseScrapper
from .core.baseScrapper import getAndCheckEnvVars, printScrapperTitle
from .services.selenium.seleniumService import SeleniumService
from .services.selenium.browser_service import sleep
from .util.persistence_manager import PersistenceManager
from .navigator.indeedNavigator import IndeedNavigator
from .services.IndeedService import IndeedService
from commonlib.terminalColor import green, yellow, printHR, red
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.stringUtil import join

USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("INDEED")

# Set to True to stop selenium driver navigating if any error occurs
DEBUG = True

WEB_PAGE = "Indeed"
JOBS_X_PAGE = 16 # usually 1 row is hidden
LOCATION = "España"
REMOTE = True
DAYS_OLD = 3

print("Indeed scrapper init")
navigator: IndeedNavigator = None
service: IndeedService = None


def run(seleniumUtil: SeleniumService, preloadPage: bool, persistenceManager: PersistenceManager = None):
    """Login, process jobs in search paginated list results"""
    global navigator, service
    navigator = IndeedNavigator(seleniumUtil)
    printScrapperTitle("Indeed", preloadPage)
    if preloadPage:
        navigator.login()
        return
    saved_state = persistenceManager.get_state("Indeed")
    saved_keyword = saved_state.get("keyword")
    saved_page = saved_state.get("page", 1)
    skip = True if saved_keyword else False
    with MysqlUtil() as mysql:
        service = IndeedService(mysql, persistenceManager)
        service.set_debug(DEBUG)
        for keywords in JOBS_SEARCH.split(","):
            keyword = keywords.strip()
            start_page = 1
            if saved_keyword:
                if saved_keyword == keyword:
                    skip = False
                    start_page = saved_page
                elif skip:
                    print(yellow(f"Skipping keyword '{keyword}' (already processed)"))
                    continue
            try:
                search_jobs(keyword, start_page)
                persistenceManager.remove_failed_keyword("Indeed", keyword)
            except Exception:
                baseScrapper.debug(DEBUG)
                persistenceManager.add_failed_keyword("Indeed", keyword)
    persistenceManager.finalize_scrapper("Indeed")


def search_jobs(keywords: str, startPage: int = 1):
    sleep(3,4)
    print(yellow(f"Search keyword={keywords}"))
    navigator.search(keywords, LOCATION, REMOTE, DAYS_OLD, startPage)
    sleep(3,4)
    navigator.wait_until_page_is_loaded()
    navigator.clickSortByDate()
    sleep(3,4)
    navigator.wait_until_page_is_loaded()

    page = 0
    currentItem = 0
    totalResults = navigator.get_total_results_from_header(keywords)
    if totalResults==0:
        print(yellow(f"There are no results for search={keywords}"))
        return
    # Fast forward
    if startPage > 1:
        print(yellow(f"Fast forwarding to page {startPage}..."))
        while page < startPage - 1:
            if navigator.click_next_page():
                page += 1
                navigator.wait_until_page_is_loaded()
                sleep(1, 2)
            else:
                break
    totalPages = totalResults/JOBS_X_PAGE if totalResults % JOBS_X_PAGE == 0 else totalResults/JOBS_X_PAGE + 1
    while True:
        page += 1
        baseScrapper.printPage(WEB_PAGE, page, totalPages, keywords)
        idx = 0
        newJobFound = False
        while idx < JOBS_X_PAGE:
            print(green(f"pg {page} job {idx + 1} - "), end="")
            if load_and_process_row(idx):
                newJobFound = True
            currentItem += 1
            print()
            idx += 1
        if not newJobFound:
            print(yellow("No new jobs found in this page, stopping keyword processing."))
            break
        if navigator.click_next_page():
            navigator.wait_until_page_is_loaded()
            sleep(5, 6)
            service.update_state(keywords, page + 1)
        else:
            break
    summarize(keywords, totalResults, currentItem)


def summarize(keywords, totalResults, currentItem):
    printHR()
    print(f"{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords}")
    printHR()
    print()


def load_and_process_row(idx) -> bool:
    """Return true if job was inserted"""
    ignore = True
    jobExists = False
    url = ""
    try:
        navigator.close_modal()
        if not navigator.scroll_jobs_list(idx):
            return False
        sleep(0.5, 1)
        jobLinkElm = navigator.get_job_link_element(idx)
        # Get initial URL from link for job ID extraction
        initial_url = navigator.get_job_url(jobLinkElm)
        jobId, jobExists = service.job_exists_in_db(initial_url)
        if jobExists:
            print(yellow(f"Job id={jobId} already exists in DB, IGNORED."), end="", flush=True)
            return False
        # Load the job detail page
        navigator.load_job_detail(jobLinkElm)
        # Get the actual URL from the main page after navigation
        sleep(2, 2)
        url = navigator.selenium.getUrl()
        ignore = False
    except IndexError as ex:
        print(yellow(f"WARNING: could not get all items per page, that's expected because not always has {JOBS_X_PAGE} pages: {ex}"), end='')
    except Exception:
        baseScrapper.debug(DEBUG)
    if not ignore:
        if not process_row(url):
            print(red("Validation failed"))
            return load_and_process_row(idx)
        sleep(1, 2)
        return True
    return False


@retry(raiseException=False)
def process_row(url):
    title, company, location, html = navigator.get_job_data()
    easyApply = navigator.check_easy_apply()
    return service.process_job(title, company, location, url, html, easyApply)
