from typing import List

import re
import unicodedata

CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = ".jobsearch-JobCountAndSortPane-jobCount > span:nth-child(1)"
CSS_SEL_JOB_COUNT = ".jobsearch-JobCountAndSortPane-jobCount"
CSS_SEL_JOB_LI = ".job_seen_beacon"
CSS_SEL_JOB_LINK = ".jobTitle a, .jobTitle > a, h2.jobTitle > a, td.resultContent > div > h2 > a"
CSS_SEL_NEXT_PAGE_BUTTON = 'a[data-testid="pagination-page-next"]'

CSS_SEL_JOB_TITLE = ["[data-testid='vj-job-title']", "[data-testid='company-info-title-row'] h5", "h1.jobsearch-JobInfoHeader-title", "h2.jobsearch-JobInfoHeader-title", "div.jobsearch-JobInfoHeader-title-container h2", "[data-testid='jobsearch-JobInfoHeader-title']", ".jobsearch-JobInfoHeader-title", "h1", "h5"]
CSS_SEL_COMPANY = ["[data-testid='vj-company-name']", '[data-testid="company-info-metadata"] a[href*="/cmp/"]', 'div[data-testid="inlineHeader-companyName"]', "[data-testid='jobsearch-JobInfoHeader-companyName']", ".jobsearch-InlineCompanyRating div", ".jobsearch-CompanyReview--inline-rating div", ".jobsearch-InlineCompanyRating-companyName", "div.jobsearch-JobInfoHeader-subtitle > div > div > div:first-child"]
DELISTED_TITLE = "No podemos encontrar esta página"
CSS_SEL_LOCATION = ['div[data-testid="inlineHeader-companyLocation"]', "[data-testid='jobsearch-JobInfoHeader-companyLocation']", ".jobsearch-JobInfoHeader-subtitle div:last-child", ".jobsearch-JobInfoHeader-subtitle > div > div", ".jobsearch-JobInfoHeader-subtitle > div"]
CSS_SEL_JOB_SALARY = ["[data-testid='salary-snippet-container']", "div[aria-label=Salario] span", "#salaryInfoAndJobType"]
CSS_SEL_JOB_DESCRIPTION = [".simple-job-description-html", ".react-native-html-content", "#jobDescriptionText", ".jobsearch-jobDescriptionText", ".jobsearch-JobComponent-description", ".jobsearch-ViewJobLayout-jobDescription"]
CSS_SEL_JOB_EASY_APPLY = ["[data-testid='viewjob-indeed-apply']", "#jobsearch-ViewJobButtons-container span.indeed-apply-status-not-applied button", "button.indeed-apply-button", ".indeed-apply-button", "[data-testid='jobsearch-ViewJobButtons-container'] button"]

_TOTAL_RESULT_SELECTORS = [CSS_SEL_JOB_COUNT, ".jobsearch-JobCountAndSortPane-jobCount span", ".jobsearch-DesktopJobCount", "div[class*='jobCount']"]

_MODALITY_TOKENS = {"teletrabajo", "remoto", "remote", "trabajo hibrido", "hibrido", "hybrid", "trabajo presencial", "presencial", "on site", "onsite", "onsite remote"}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).casefold().strip()


def _extract_text(page, selectors: List[str], suffix: str = "") -> str:
    for sel in selectors:
        text = page.css(f"{sel} ::text").get()
        if not text:
            text = page.css(f"{sel} *::text").get()
        if text:
            return str(text).strip() + suffix
    return ""


def _extract_location(page) -> str:
    if text := _extract_text(page, CSS_SEL_LOCATION):
        return text
    for el in page.css('[data-testid="company-info-metadata"] div[dir="ltr"]'):
        text = (el.get_all_text() or "").strip()
        if "," in text and not el.css("a"):
            return text
    return ""


def _modality_badge(page) -> str:
    def normalize(text):
        return _normalize(text)

    try:
        candidates = page.css("[data-testid='company-info-metadata'] div")
    except Exception:
        return ""
    try:
        candidate_list = list(candidates)
    except TypeError:
        candidate_list = []
    for el in candidate_list:
        try:
            text = (getattr(el, "get_all_text", lambda: "")() or "").strip()
        except Exception:
            text = str(el).strip()
        if normalize(text) in _MODALITY_TOKENS:
            return text
    return ""


def _extract_total_from_title(page) -> int:
    match = re.match(r"([\d.,]+)\s+empleos", str(page.css("title::text").get() or "").strip())
    return int(match.group(1).replace(".", "").replace(",", "")) if match else 0
