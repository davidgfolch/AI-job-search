
import math
import re
import traceback
from typing import Optional

from markdownify import MarkdownConverter
import urllib.parse
from commonlib.environmentUtil import getEnv
from commonlib.stringUtil import hasLenAnyText
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.terminalColor import green, printHR, red, yellow
from ..services.selenium.browser_service import sleep
from ..navigator.baseNavigator import BaseNavigator


def getAndCheckEnvVars(site: str):
    mail = getEnv(f'{site}_EMAIL')
    pwd = getEnv(f'{site}_PWD')
    search = getEnv(f'{site}_JOBS_SEARCH')
    if not search:
        search = getEnv('JOBS_SEARCH')
    if not mail or not pwd or not search:
        print(yellow('Set up .venv file with the following keys:'))
        print(yellow(f'{site}_EMAIL' if not mail else '',
                     f'{site}_PWD' if not pwd else '',
                     f'{site}_JOBS_SEARCH' if not search else ''))
        print(yellow('Please read README.md for more info'))
        exit()
    return mail, pwd, search


def printScrapperTitle(scrapper: str, preloadPage: bool):
    printHR(green)
    if preloadPage:
        print(yellow(f'{getDatetimeNowStr()} - PRELOADING {scrapper}: login & security filters'))
    else:
        print(green(f'{getDatetimeNowStr()} - RUNNING {scrapper} scrapper'))
    printHR(green)


def printPage(webPage, page, totalPages, keywords):
    print(green(f'{getDatetimeNowStr()}- {webPage} Starting page {page} of {totalPages} ',
                f'search={keywords}'))
    printHR(green)

class CustomConverter(MarkdownConverter):
    def convert_br(self, el, text, parent_tags):
        # Usa dos espacios + salto de línea para Markdown compatible
        return "  \n"

    def convert_strong(self, el, text, parent_tags):
        # markdownify strips newlines, but we want and space after last bold mark **, to show the bold text properly
        if text:
            text = text.replace('\n', ' ')
        return super().convert_strong(el, text, parent_tags)+' '
    
    def convert_ul(self, el, text, parent_tags):
        return super().convert_ul(el, text, parent_tags)+'\n'
    
def htmlToMarkdown(html: str) -> str:
    md = CustomConverter().convert(html)
    return removeInvalidScapes(md)


def removeInvalidScapes(md: str) -> str:
    md = md.replace('\$', '$')  # dont remove \$ ignore the warning
    # remove all backslash NOT unicode \uxxxx and NOT markdown standard escapes
    md = re.sub(r'\\(?!(u[0-9a-fA-F]{4}|[\\`*_{}\[\]()#+\-.!]))', '', md, flags=re.M)
    return md


def removeLinks(md: str) -> str:
    # remove all links, but keep the text
    return re.sub(r'\[([^\]]+)\]\([^\)]+\)', r' \1 ', md, flags=re.M)


def validate(title: str, url: str, company: str, markdown: str, debugFlag: bool):
    fields = ['title', 'url', 'company', 'markdown']
    validations = hasLenAnyText(title, url, company, markdown)
    if 0 in validations:
        for i, v in enumerate(validations):
            debug(debugFlag, "validate -> " +
                  red(f'ERROR: empty required field {fields[i]}, ') +
                  yellow(f' -> Url: {url} '))
        return False
    return True



from .utils import debug

def join(*str: str) -> str:
    return ''.join(str)


def removeUrlParameter(url: str, parameter: str) -> str:
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if parameter in qs:
        del qs[parameter]
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def pageExists(page: int, totalResults: int, jobsXPage: int) -> bool:
    return page > 1 and totalResults > 0 and page < math.ceil(totalResults / jobsXPage)


def fast_forward_page(navigator: BaseNavigator, start_page: int, total_results: int, jobs_x_page: int) -> int:
    """
    Fast forwards to the start_page by clicking next page button.
    Returns the page number reached (usually start_page).
    """
    page = 1
    if start_page > 1 and pageExists(start_page, total_results, jobs_x_page):
        print(yellow(f"Fast forwarding to page {start_page}..."))
        while page < start_page:
            if navigator.click_next_page():
                page += 1
                navigator.wait_until_page_is_loaded()
                sleep(1, 2)
            else:
                break
    return page


def summarize(keywords, totalResults, currentItem):
    printHR()
    print(f'{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords}')
    printHR()
    print()
