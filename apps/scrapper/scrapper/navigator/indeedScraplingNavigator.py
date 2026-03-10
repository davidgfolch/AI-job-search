from typing import List, Tuple
import re
from urllib.parse import quote, parse_qs, urlparse

from commonlib.terminalColor import green, yellow, red, printHR
from commonlib.stringUtil import join as str_join
from .baseNavigator import BaseNavigator
from ..services.scrapling.scraplingService import ScraplingService

CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = ".jobsearch-JobCountAndSortPane-jobCount > span:nth-child(1)"
CSS_SEL_JOB_COUNT = ".jobsearch-JobCountAndSortPane-jobCount"
CSS_SEL_JOB_LI = ".job_seen_beacon"
CSS_SEL_JOB_LINK = ".jobTitle a, .jobTitle > a, h2.jobTitle > a, td.resultContent > div > h2 > a"
CSS_SEL_NEXT_PAGE_BUTTON = 'a[data-testid="pagination-page-next"]'

CSS_SEL_JOB_TITLE = ["h1.jobsearch-JobInfoHeader-title", "h2.jobsearch-JobInfoHeader-title", "div.jobsearch-JobInfoHeader-title-container h2", "[data-testid='jobsearch-JobInfoHeader-title']", ".jobsearch-JobInfoHeader-title", "h1"]
CSS_SEL_COMPANY = ['div[data-testid="inlineHeader-companyName"]', "[data-testid='jobsearch-JobInfoHeader-companyName']", ".jobsearch-InlineCompanyRating div", ".jobsearch-CompanyReview--inline-rating div", ".jobsearch-InlineCompanyRating-companyName", "div.jobsearch-JobInfoHeader-subtitle > div > div > div:first-child"]
CSS_SEL_LOCATION = ['div[data-testid="inlineHeader-companyLocation"]', "[data-testid='jobsearch-JobInfoHeader-companyLocation']", ".jobsearch-JobInfoHeader-subtitle div:last-child", ".jobsearch-JobInfoHeader-subtitle > div > div", ".jobsearch-JobInfoHeader-subtitle > div"]
CSS_SEL_JOB_DESCRIPTION = ["#jobDescriptionText", ".jobsearch-jobDescriptionText", ".jobsearch-JobComponent-description", ".jobsearch-ViewJobLayout-jobDescription"]
CSS_SEL_JOB_EASY_APPLY = ["#jobsearch-ViewJobButtons-container span.indeed-apply-status-not-applied button", "button.indeed-apply-button", ".indeed-apply-button", "[data-testid='jobsearch-ViewJobButtons-container'] button"]

_TOTAL_RESULT_SELECTORS = [CSS_SEL_JOB_COUNT, ".jobsearch-JobCountAndSortPane-jobCount span", ".jobsearch-DesktopJobCount", "div[class*='jobCount']"]


def _extract_text(page, selectors: List[str], suffix: str = "") -> str:
    for sel in selectors:
        text = page.css(f"{sel}::text").get()
        if not text:
            text = page.css(f"{sel} *::text").get()
        if text:
            return str(text).strip() + suffix
    return ""


class IndeedScraplingNavigator(BaseNavigator):
    def __init__(self, proxies: List[str], debug=False):
        scrapling_service = ScraplingService(proxies, debug)
        super().__init__(scrapling_service, debug)
        self.scrapling_service: ScraplingService = scrapling_service

    def checkNoResults(self):
        if not self.current_page:
            return True
        return len(self.current_page.css(".jobsearch-NoResult-messageContainer")) > 0

    def clickSortByDate(self):
        pass

    def search(self, keyword: str, location: str, remote: bool, daysOld: int, startPage: int):
        print(f'Searching for "{keyword}" in "{location}" (Scrapling)')
        encoded_keyword, encoded_location = quote(keyword), quote(location)
        url = f"https://es.indeed.com/jobs?q={encoded_keyword}&l={encoded_location}&fromage={daysOld}"
        print(f"Scrapling: Navigating to {url}")
        self.current_page = self.scrapling_service.fetch_with_retry(url)
        if self.current_page.status == 429 or "Just a moment" in (self.current_page.css('title::text').get() or ""):
            print(red("Detected 429 or Captcha block. Resetting session..."))
            self.scrapling_service.reset_session()
            self.current_page = self.scrapling_service.fetch_with_retry(url)
        if "from=gnav-jobsearch" in self.current_page.url or self.current_page.url == "https://es.indeed.com/":
            print(yellow("Detected redirect to home page, retrying search with direct parameters..."))
            url = f"https://es.indeed.com/jobs?q={encoded_keyword}&l={encoded_location}"
            self.current_page = self.scrapling_service.fetch_with_retry(url)
            if "from=gnav-jobsearch" in self.current_page.url:
                print(yellow("Still redirected. Resetting session..."))
                self.scrapling_service.reset_session()
                self.current_page = self.scrapling_service.fetch_with_retry(url)
        if self.debug:
            print(f"DEBUG: Current URL after search: {self.current_page.url}")
            print(f"DEBUG: Page title: {self.current_page.css('title::text').get()}")

    def get_total_results(self, keywords: str) -> int:
        if not self.current_page:
            return 0
        total_text = None
        for sel in _TOTAL_RESULT_SELECTORS:
            total_text = self.current_page.css(f"{sel}::text").get()
            if total_text:
                if self.debug:
                    print(f"DEBUG: Found total text with selector {sel}: {total_text}")
                break
        if not total_text:
            if self.debug:
                print(yellow("DEBUG: Could not find total results text. Checking for job links..."))
            return 0
        nums = re.findall(r'[0-9.,]+', total_text)
        if not nums:
            return 0
        total = nums[0]
        printHR()
        print(green(str_join(f"{total} total results for search: {keywords}")))
        printHR()
        return int(total.replace(".", "").replace(",", ""))

    def fast_forward_page(self, start_page: int, total_results: int, jobs_x_page: int) -> int:
        if start_page > 1:
            start_num = (start_page - 1) * 10
            url = self.current_page.url
            url = re.sub(r"&start=\d+", f"&start={start_num}", url) if "&start=" in url else url + f"&start={start_num}"
            self.current_page = self.scrapling_service.fetch(url)
        return start_page

    def get_page_job_links(self) -> List[str]:
        if not self.current_page:
            return []
        links = []
        for el in self.current_page.css(CSS_SEL_JOB_LI):
            link_el = el.css(CSS_SEL_JOB_LINK)
            if link_el:
                href = link_el[0].attrib.get("href")
                if href:
                    links.append(("https://es.indeed.com" if href.startswith("/") else "") + href)
        return links

    def click_next_page(self) -> bool:
        if not self.current_page:
            return False
        next_btns = self.current_page.css(CSS_SEL_NEXT_PAGE_BUTTON)
        if not next_btns:
            return False
        href = next_btns[0].attrib.get("href")
        if not href:
            return False
        url = "https://es.indeed.com" + href if href.startswith("/") else href
        self.current_page = self.scrapling_service.fetch(url)
        return True

    def scroll_jobs_list(self, idx: int):
        pass

    def load_job_detail(self, url: str):
        if self.current_page and self.current_page.url == url:
            return
        print(yellow(f"loading detail: {url}...") if self.debug else yellow("loading..."), end="")
        self.current_page = self.scrapling_service.fetch(url)

    def get_current_job_url(self) -> str:
        return self.current_page.url if self.current_page else ""

    def get_job_data(self) -> Tuple[str, str, str, str, str]:
        title = _extract_text(self.current_page, CSS_SEL_JOB_TITLE, "\n- job post").removesuffix("\n- job post")
        if not title:
            h1, h2 = self.current_page.css("h1 *::text").get(), self.current_page.css("h2 *::text").get()
            title = (h1 or h2 or "").strip()
        company = _extract_text(self.current_page, CSS_SEL_COMPANY)
        location = _extract_text(self.current_page, CSS_SEL_LOCATION)
        html = next((str(desc_el.get()) for sel in CSS_SEL_JOB_DESCRIPTION if (desc_el := self.current_page.css(sel))), "")
        url = self.get_current_job_url()
        if not title or not company:
            query = parse_qs(urlparse(url).query)
            if not title and 't' in query:
                title = query['t'][0]
            if not company and 'cmp' in query:
                company = query['cmp'][0]
        if self.debug:
            print(f"DEBUG: Scraped detail -> Title: {title[:30] if title else 'EMPTY'}, Company: {company}, Location: {location}")
        return title or "", company or "", location or "", url, html

    def check_easy_apply(self) -> bool:
        return any(self.current_page.css(sel) for sel in CSS_SEL_JOB_EASY_APPLY)

    def shutdown(self):
        self.scrapling_service.shutdown()
