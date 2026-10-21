import re
from typing import List, Tuple
from urllib.parse import quote, parse_qs, urlparse

from commonlib.observability import get_logger
from commonlib.stringUtil import join
from commonlib.terminalColor import green, yellow, red, printHR
from .baseNavigator import BaseNavigator
from ..services.scrapling.scraplingService import ScraplingService
from .indeedScrapling_elements import (
    CSS_SEL_JOB_COUNT, CSS_SEL_JOB_LI, CSS_SEL_JOB_LINK, CSS_SEL_NEXT_PAGE_BUTTON,
    CSS_SEL_JOB_TITLE, CSS_SEL_COMPANY, CSS_SEL_JOB_SALARY,
    CSS_SEL_JOB_DESCRIPTION, CSS_SEL_JOB_EASY_APPLY, DELISTED_TITLE,
    _extract_text, _extract_location, _modality_badge, _extract_total_from_title,
)

logger = get_logger("scrapper.indeedScraplingNavigator")


class IndeedScraplingNavigator(BaseNavigator):
    def __init__(self, proxies: List[str], debug=False):
        scrapling_service = ScraplingService(proxies, debug)
        super().__init__(scrapling_service, debug)
        self.scrapling_service: ScraplingService = scrapling_service

    def checkNoResults(self):
        if not self.current_page:
            return True
        return len(self.current_page.css(".jobsearch-NoResult-messageContainer")) > 0

    def is_delisted(self) -> bool:
        if not self.current_page:
            return False
        if getattr(self.current_page, "status", None) == 404:
            return True
        return _extract_text(self.current_page, ["h1"], "") == DELISTED_TITLE

    def clickSortByDate(self):
        pass

    def search(self, keyword: str, location: str, remote: bool, daysOld: int, startPage: int):  # noqa: ARG002 - navigator interface
        logger.info("indeed.scrapling.search.started", keyword=keyword, location=location,
                    console=f'Searching for "{keyword}" in "{location}" (Scrapling)')
        encoded_keyword, encoded_location = quote(keyword), quote(location)
        url = f"https://es.indeed.com/jobs?q={encoded_keyword}&l={encoded_location}&fromage={daysOld}"
        logger.info("indeed.scrapling.navigating", url=url, console=f"Scrapling: Navigating to {url}")
        self.current_page = self.scrapling_service.fetch_with_retry(url)
        if self.current_page.status == 429 or "Just a moment" in (self.current_page.css('title::text').get() or ""):
            logger.warning("indeed.scrapling.block_detected", status=429, console=red("Detected 429 or Captcha block. Resetting session..."))
            self.scrapling_service.reset_session()
            self.current_page = self.scrapling_service.fetch_with_retry(url)
        if "from=gnav-jobsearch" in self.current_page.url or self.current_page.url == "https://es.indeed.com/":
            logger.warning("indeed.scrapling.redirect_to_home_detected", console=yellow("Detected redirect to home page, retrying search with direct parameters..."))
            url = f"https://es.indeed.com/jobs?q={encoded_keyword}&l={encoded_location}"
            self.current_page = self.scrapling_service.fetch_with_retry(url)
            if "from=gnav-jobsearch" in self.current_page.url:
                logger.warning("indeed.scrapling.redirect_persisted", action="session_reset", console=yellow("Still redirected. Resetting session..."))
                self.scrapling_service.reset_session()
                self.current_page = self.scrapling_service.fetch_with_retry(url)
        if self.debug:
            logger.debug("indeed.scrapling.search_context", url=self.current_page.url, page_title=self.current_page.css('title::text').get(),
                          console=f'DEBUG: Current URL after search: {self.current_page.url}\n'
                          f'DEBUG: Page title: {self.current_page.css("title::text").get()}')

    def get_total_results(self, keywords: str) -> int:
        if not self.current_page:
            return 0
        total_text = None
        for sel in [CSS_SEL_JOB_COUNT, ".jobsearch-JobCountAndSortPane-jobCount span", ".jobsearch-DesktopJobCount", "div[class*='jobCount']"]:
            total_text = self.current_page.css(f"{sel}::text").get()
            if total_text:
                if self.debug:
                    logger.debug("indeed.scrapling.total_text_found", selector=sel, total_text=total_text,
                                  console=f"DEBUG: Found total text with selector {sel}: {total_text}")
                break
        if not total_text:
            if total_from_title := _extract_total_from_title(self.current_page):
                total_text = f"{total_from_title} empleos"
            else:
                if self.debug:
                    logger.debug("indeed.scrapling.total_text_not_found", fallback="job_links",
                                  console=yellow("DEBUG: Could not find total results text. Checking for job links..."))
                return 0
        nums = re.findall(r'[0-9.,]+', total_text)
        if not nums:
            return 0
        total = nums[0]
        printHR()
        logger.info("indeed.scrapling.results_found", total=total, keywords=keywords, console=green(join(f"{total} total results for search: {keywords}")))
        printHR()
        return int(total.replace(".", "").replace(",", ""))

    def fast_forward_page(self, start_page: int, total_results: int, jobs_x_page: int) -> int:  # noqa: ARG002 - navigator interface
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
        logger.info("indeed.scrapling.detail_loading", url=url, console=yellow(f"loading detail: {url}...") if self.debug else yellow("loading..."))
        self.current_page = self.scrapling_service.fetch(url)

    def get_current_job_url(self) -> str:
        return self.current_page.url if self.current_page else ""

    def get_job_data(self) -> Tuple[str, str, str, str, str, str]:
        title = _extract_text(self.current_page, CSS_SEL_JOB_TITLE, "\n- job post").removesuffix("\n- job post")
        if not title:
            title = next((t for sel in ("h1", "h2", "h5") if (t := self.current_page.css(f"{sel} *::text").get())), "").strip()
        company = _extract_text(self.current_page, CSS_SEL_COMPANY)
        location = _extract_location(self.current_page)
        html = next((str(desc_el.get()) for sel in CSS_SEL_JOB_DESCRIPTION if (desc_el := self.current_page.css(sel))), "")
        badge = _modality_badge(self.current_page)
        if badge:
            html = ("Modalidad de trabajo: " + badge + "\n\n" + (html or "")).strip()
        salary = _extract_text(self.current_page, CSS_SEL_JOB_SALARY)
        url = self.get_current_job_url()
        if not title or not company:
            query = parse_qs(urlparse(url).query)
            if not title and 't' in query:
                title = query['t'][0]
            if not company and 'cmp' in query:
                company = query['cmp'][0]
        if self.debug:
            logger.debug("indeed.scrapling.detail_scraped", title=title[:30] if title else 'EMPTY', company=company, location=location,
                          console=f"DEBUG: Scraped detail -> Title: {title[:30] if title else 'EMPTY'}, Company: {company}, Location: {location}")
        return title or "", company or "", location or "", salary or "", url, html

    def check_easy_apply(self) -> bool:
        return any(self.current_page.css(sel) for sel in CSS_SEL_JOB_EASY_APPLY)

    def close(self):
        self.scrapling_service.close()
