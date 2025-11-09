import math
import re
from typing import List, Dict, Any
from urllib.parse import quote
from selenium.common.exceptions import NoSuchElementException
from ..interfaces.scrapper_interface import ScrapperInterface
from ..seleniumUtil import SeleniumUtil
from ..baseScrapper import getAndCheckEnvVars, htmlToMarkdown, join, printPage, validate
from ..selectors.linkedinSelectors import *
from commonlib.terminalColor import green, yellow, red
from commonlib.decorator.retry import retry

class LinkedInScrapper(ScrapperInterface):
    """LinkedIn scrapper implementation following SOLID principles"""
    
    def __init__(self):
        self.user_email, self.user_pwd, self.jobs_search = getAndCheckEnvVars("LINKEDIN")
        self.remote = '2'  # remote work
        self.location = '105646813'  # Spain
        self.f_tpr = 'r86400'  # last 24 hours
        self.jobs_per_page = 25
        self.web_page = 'LinkedIn'
    
    def get_site_name(self) -> str:
        return self.web_page
    
    def login(self, selenium: SeleniumUtil) -> bool:
        """Login to LinkedIn"""
        try:
            selenium.loadPage('https://www.linkedin.com/login')
            selenium.sendKeys('#username', self.user_email)
            selenium.sendKeys('#password', self.user_pwd)
            
            try:
                selenium.checkboxUnselect('div.remember_me__opt_in input')
            except Exception:
                pass
            
            selenium.waitAndClick('form button[type=submit]')
            
            print(yellow('Waiting for LinkedIn to redirect to feed page...'))
            selenium.waitUntilPageUrlContains('https://www.linkedin.com/feed/', 60)
            return True
            
        except Exception as e:
            print(red(f"Login failed: {e}"))
            return False
    
    def search_jobs(self, selenium: SeleniumUtil, keywords: str) -> List[Dict[str, Any]]:
        """Search for jobs with given keywords"""
        jobs = []
        
        try:
            url = self._build_search_url(keywords)
            print(yellow(f'Loading page {url}'))
            selenium.loadPage(url)
            selenium.waitUntilPageIsLoaded()
            
            if not self._check_results(selenium, keywords, url):
                return jobs
            
            self._hide_ui_elements(selenium)
            total_results = self._get_total_results(selenium, keywords)
            total_pages = math.ceil(total_results / self.jobs_per_page)
            
            page = 1
            current_item = 0
            
            while True:
                printPage(self.web_page, page, total_pages, keywords)
                page_jobs = self._process_page(selenium, page, current_item, total_results)
                jobs.extend(page_jobs)
                current_item += len(page_jobs)
                
                if current_item >= total_results or page >= total_pages or not self._click_next_page(selenium):
                    break
                
                page += 1
                selenium.waitUntilPageIsLoaded()
            
            self._print_summary(keywords, total_results, current_item)
            
        except Exception as e:
            print(red(f'Error searching jobs: {e}'))
        
        return jobs
    
    def extract_job_data(self, selenium: SeleniumUtil, job_element) -> Dict[str, Any]:
        """Extract job data from a job element"""
        # This method is used by search_jobs internally
        pass
    
    def _build_search_url(self, keywords: str) -> str:
        """Build search URL with parameters"""
        return join('https://www.linkedin.com/jobs/search/?',
                   '&'.join([
                       f'keywords={quote(keywords)}',
                       f'f_WT={self.remote}',
                       f'geoId={self.location}',
                       f'f_TPR={self.f_tpr}'
                   ]))
    
    def _check_results(self, selenium: SeleniumUtil, keywords: str, url: str) -> bool:
        """Check if search has results"""
        no_result_elms = selenium.getElms(CSS_SEL_NO_RESULTS)
        if len(no_result_elms) > 0:
            print(red(f'No results for keywords={keywords} URL={url}'))
            return False
        return True
    
    def _hide_ui_elements(self, selenium: SeleniumUtil):
        """Hide UI elements that might interfere"""
        selenium.waitAndClick_noError(CSS_SEL_MESSAGES_HIDE, 'Could not collapse messages')
    
    def _get_total_results(self, selenium: SeleniumUtil, keywords: str) -> int:
        """Get total number of results"""
        total_text = selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
        total = int(total_text.replace('+', ''))
        print(green(f'{total} total results for search: {keywords}'))
        return total
    
    def _process_page(self, selenium: SeleniumUtil, page: int, current_item: int, total_results: int) -> List[Dict[str, Any]]:
        """Process all jobs on current page"""
        jobs = []
        errors = 0
        
        for idx in range(1, self.jobs_per_page + 1):
            if current_item + idx > total_results:
                break
            
            print(green(f'pg {page} job {idx} - '), end='')
            job_data = self._process_job_item(selenium, idx)
            
            if job_data:
                jobs.append(job_data)
            else:
                errors += 1
                if errors > 1:  # Exit page loop if too many errors
                    break
        
        return jobs
    
    def _process_job_item(self, selenium: SeleniumUtil, idx: int) -> Dict[str, Any]:
        """Process individual job item"""
        try:
            css_sel = self._scroll_to_job(selenium, idx)
            job_data = self._extract_job_info(selenium, idx, css_sel)
            
            if job_data and validate(job_data['title'], job_data['url'], 
                                   job_data['company'], job_data['markdown'], False):
                return job_data
            
        except Exception as e:
            print(red(f'Error processing job {idx}: {e}'))
        
        return None
    
    def _scroll_to_job(self, selenium: SeleniumUtil, idx: int) -> str:
        """Scroll to job item and return CSS selector"""
        css_sel = self._replace_index(CSS_SEL_JOB_LINK, idx)
        
        try:
            selenium.scrollIntoView(css_sel)
        except NoSuchElementException:
            self._scroll_jobs_list_retry(selenium, idx)
            selenium.scrollIntoView(css_sel)
        
        selenium.moveToElement(selenium.getElm(css_sel))
        selenium.waitUntilClickable(css_sel)
        return css_sel
    
    def _extract_job_info(self, selenium: SeleniumUtil, idx: int, css_sel: str) -> Dict[str, Any]:
        """Extract job information from page"""
        li_prefix = self._replace_index(CSS_SEL_JOB_LI_IDX, idx)
        
        title = selenium.getText(f'{li_prefix} {LI_JOB_TITLE_CSS_SUFFIX}')
        company = selenium.getText(f'{li_prefix} {CSS_SEL_COMPANY}')
        location = selenium.getText(f'{li_prefix} {CSS_SEL_LOCATION}')
        
        selenium.waitUntilClickable(CSS_SEL_JOB_HEADER)
        url = self._get_job_url_short(selenium.getAttr(CSS_SEL_JOB_HEADER, 'href'))
        job_id = self._get_job_id(url)
        
        # Load job details if needed
        if idx != 1:  # First job loads automatically
            print(yellow('loading...'), end='')
            selenium.waitAndClick(css_sel)
        
        html = selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        markdown = htmlToMarkdown(html)
        easy_apply = len(selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
        
        print(f'{job_id}, {title}, {company}, {location}, easy_apply={easy_apply} - ', end='')
        
        return {
            'job_id': job_id,
            'title': title,
            'company': company,
            'location': location,
            'url': url,
            'markdown': markdown,
            'easy_apply': easy_apply,
            'web_page': self.web_page
        }
    
    @retry(exception=NoSuchElementException, raiseException=False)
    def _click_next_page(self, selenium: SeleniumUtil) -> bool:
        """Click next page button"""
        selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
        return True
    
    @retry()
    def _scroll_jobs_list_retry(self, selenium: SeleniumUtil, idx: int):
        """Retry scrolling to job list item"""
        css_sel_i = self._replace_index(CSS_SEL_JOB_LI_IDX, idx)
        selenium.scrollIntoView(css_sel_i)
        selenium.moveToElement(selenium.getElm(css_sel_i))
        selenium.waitUntilClickable(self._replace_index(CSS_SEL_JOB_LINK, idx))
    
    def _replace_index(self, css_selector: str, idx: int) -> str:
        """Replace index placeholder in CSS selector"""
        return css_selector.replace('##idx##', str(idx))
    
    def _get_job_id(self, url: str) -> int:
        """Extract job ID from URL"""
        return int(re.sub(r'.*/jobs/view/([^/]+)/.*', r'\1', url))
    
    def _get_job_url_short(self, url: str) -> str:
        """Get shortened job URL"""
        return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)
    
    def _print_summary(self, keywords: str, total_results: int, current_item: int):
        """Print scrapping summary"""
        print(f'Loaded {current_item} of {total_results} total results for search: {keywords}')