import re
from typing import Tuple, Optional
from commonlib.observability import get_logger
from selenium.common.exceptions import NoSuchElementException
from ...services.selenium.browser_service import sleep

logger = get_logger("scrapper.linkedinDetailReader")

JOB_URL_RE = r'/jobs/view/(\d+)'

# JOB DETAIL: right pane, same layout for list clicks and direct currentJobId urls
CSS_SEL_JOB_DETAIL = 'main > div > div:nth-child(2) > div > div:nth-child(2) > div > div > div > div > div > div[componentkey]'
CSS_SEL_JOB_TITLE_LINK = f'{CSS_SEL_JOB_DETAIL} a[href*="/jobs/view/"]'
CSS_SEL_DETAIL_COMPANY = f'{CSS_SEL_JOB_DETAIL} p a[href*="/company/"]'
CSS_SEL_DETAIL_LOCATION = f'{CSS_SEL_JOB_DETAIL} div:has(> div a[href*="/jobs/view/"]) > p > span:first-child'
CSS_SEL_DETAIL_LOCATION_WIDE = f'{CSS_SEL_JOB_DETAIL} div:has(> div a[href*="/jobs/view/"]) > p'
# LinkedIn dropped the JobDetails_AboutTheJob_ id and the section carries no stable class/id, so it is anchored on
# its heading and walked up to the first wrapper holding exactly one expandable-text-box (the description body).
# The premium upsell marks the pane that must never be returned: it wraps the whole job, company and related cards.
# LEGACY stays as a fallback for a rollback of the frontend; BOX is the last resort (description text only).
CSS_SEL_JOB_DESCRIPTION_LEGACY = f'{CSS_SEL_JOB_DETAIL} div[id^="JobDetails_AboutTheJob_"]'
CSS_SEL_JOB_DESCRIPTION_BOX = f'{CSS_SEL_JOB_DETAIL} [data-testid="expandable-text-box"]'
CSS_SEL_JOB_EXPAND_BUTTONS = f'{CSS_SEL_JOB_DETAIL} button[data-testid="expandable-text-button"]'
JS_FIND_ABOUT_THE_JOB_SECTION = (
    'const pane = document.querySelector(\'[data-testid="lazy-column"]\') || document;'
    'const heading = Array.from(pane.querySelectorAll("h2, h3")).find(h => (h.textContent || "").trim().toLowerCase() === "about the job");'
    'const findSection = () => {'
    ' let el = heading ? heading.parentElement : null;'
    ' while (el && el.getAttribute("data-testid") !== "lazy-column") {'
    '  const text = el.textContent || "";'
    '  if (el.querySelectorAll(\'[data-testid="expandable-text-box"]\').length === 1 && !text.includes("Job search faster with Premium")) return el;'
    '  el = el.parentElement;'
    ' }'
    ' return null;'
    '};'
)
JS_READ_ABOUT_THE_JOB_SECTION = JS_FIND_ABOUT_THE_JOB_SECTION + 'const section = findSection(); return section ? section.innerHTML : null;'
JS_EXPAND_ABOUT_THE_JOB_SECTION = JS_FIND_ABOUT_THE_JOB_SECTION + (
    'const section = findSection() || document.querySelector(\'[id^="JobDetails_AboutTheJob_"]\'); '
    'if (section) section.querySelectorAll(\'button[data-testid="expandable-text-button"]\').forEach(b => { try { b.click(); } catch (e) {} });'
)
# aria-label matches in both list-click and direct-url mode, the bug icon only exists in list-click mode
CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} button[aria-label="Easy Apply to this job"]'
CSS_SEL_JOB_FIT_PREFERENCES = f'{CSS_SEL_JOB_DETAIL} > div:first-child a[href*="currentJobId"]'

class LinkedinDetailReader:
    """Reads the unified job detail pane; the list-click and the direct currentJobId url render the same layout."""

    def __init__(self, selenium):
        self.selenium = selenium

    def read(self) -> Tuple[str, str, str, str, str]:
        self.selenium.waitUntilClickable(CSS_SEL_JOB_TITLE_LINK)
        title = self.selenium.getText(CSS_SEL_JOB_TITLE_LINK)
        company = self.selenium.getText(CSS_SEL_DETAIL_COMPANY)
        location = self._first_text(CSS_SEL_DETAIL_LOCATION, CSS_SEL_DETAIL_LOCATION_WIDE)
        if not (title and company and location):
            raise NoSuchElementException(f'Missing job detail fields: title={bool(title)} company={bool(company)} location={bool(location)}')
        url = self.selenium.getAttr(CSS_SEL_JOB_TITLE_LINK, 'href')
        html = self._fit_preferences_html() + self._description_html()
        return title, company, location, url, html

    def job_id(self) -> Optional[str]:
        try:
            href = self.selenium.getAttr(CSS_SEL_JOB_TITLE_LINK, 'href')
        except Exception:
            return None
        match = re.search(JOB_URL_RE, href or '')
        return match.group(1) if match else None

    def wait_for_job(self, expected_job_id: str, timeout_s: int = 8) -> bool:
        for _ in range(timeout_s * 2):
            if self.job_id() == expected_job_id:
                return True
            sleep(0.5, 0.6)
        return False

    def check_easy_apply(self) -> bool:
        return len(self.selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0

    def _fit_preferences_html(self) -> str:
        buttons = self.selenium.getElms(CSS_SEL_JOB_FIT_PREFERENCES)
        return ', '.join(map(lambda b: self.selenium.getText(b), buttons))

    def _expand_description(self):
        try:
            self.selenium.driver.execute_script(JS_EXPAND_ABOUT_THE_JOB_SECTION)
        except Exception:
            pass

    def _section_html(self) -> Optional[str]:
        try:
            html = self.selenium.driver.execute_script(JS_READ_ABOUT_THE_JOB_SECTION)
        except Exception:
            return None
        return html if isinstance(html, str) and html else None

    def _all_html(self, cssSel: str) -> str:
        # Querying the selector in the page keeps the extraction consistent with the live DOM
        # and allows every matching container to contribute its HTML (instead of only the first one).
        try:
            result = self.selenium.driver.execute_script(
                'return Array.from(document.querySelectorAll(arguments[0])).map(e => e.innerHTML);',
                cssSel,
            )
        except Exception:
            result = None
        parts = []
        if isinstance(result, list):
            for html in result:
                if isinstance(html, str) and html:
                    parts.append(html)
        if parts:
            return '\n'.join(parts)
        # Preserve compatibility for mocked/legacy paths where execute_script is not backed by a real browser.
        try:
            if html := self.selenium.getHtml(cssSel):
                return html
        except Exception:
            pass
        raise NoSuchElementException(f'No HTML from {cssSel}')

    def _description_html(self) -> str:
        self._expand_description()
        if html := self._section_html():
            return html
        try:
            if html := self._all_html(CSS_SEL_JOB_DESCRIPTION_LEGACY):
                return html
        except Exception:
            pass
        # Last resort: the first expandable-text-box is the About-the-job body (the company box comes after it).
        try:
            if html := self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION_BOX):
                return html
        except Exception:
            pass
        raise NoSuchElementException('Job description not found')

    def _first_text(self, *cssSels) -> str:
        for cssSel in cssSels:
            try:
                if text := self.selenium.getText(cssSel):
                    return text
            except Exception:
                continue
        return ''
