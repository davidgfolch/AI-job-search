import math
import re
import urllib.parse
from typing import Optional
from markdownify import MarkdownConverter

from .utils import debug
from commonlib.environmentUtil import getEnv
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.observability import get_logger
from commonlib.stringUtil import hasLenAnyText
from commonlib.terminalColor import green, printHR, red, yellow
from ..services.selenium.browser_service import sleep

logger = get_logger("scrapper.baseScrapper")


def getAndCheckEnvVars(site: str, require_pwd: bool = True):
    mail = getEnv(f'SCRAPPER_{site}_EMAIL')
    pwd = getEnv(f'SCRAPPER_{site}_PWD') if require_pwd else None
    search = getEnv(f'SCRAPPER_{site}_JOBS_SEARCH')
    if not search:
        search = getEnv('SCRAPPER_JOBS_SEARCH')
    missing = []
    if not mail:
        missing.append(f'SCRAPPER_{site}_EMAIL')
    if require_pwd and not pwd:
        missing.append(f'SCRAPPER_{site}_PWD')
    if not search:
        missing.append(f'SCRAPPER_{site}_JOBS_SEARCH')
    if missing:
        logger.error("config.env_missing", site=site, missing_count=len(missing), missing_keys=missing,
                     hint="Set up .env.secrets with the listed keys, see apps/scrapper/README.md",
                     console="\n".join([yellow('Set up .venv file with the following keys:'), yellow(' '.join(missing)),
                                         yellow('Please read README.md for more info')]))
        exit()
    return mail, pwd, search


def printScrapperTitle(scrapper: str, preloadPage: bool):
    printHR(green)
    logger.info("scraper.run_starting", scrapper=scrapper, preload=bool(preloadPage),
                console=yellow(f'{getDatetimeNowStr()} - PRELOADING {scrapper}: login & security filters') if preloadPage
                else green(f'{getDatetimeNowStr()} - RUNNING {scrapper} scrapper'))
    printHR(green)


def printPage(webPage, page, totalPages, keywords):
    logger.info("scraper.page_loaded", web_page=webPage, page=page, total_pages=totalPages, keywords=keywords,
                console=green(f'{getDatetimeNowStr()}- {webPage} Starting page {page} of {totalPages} ', f'search={keywords}'))
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
            if v:
                continue
            debug(debugFlag, "validate -> " + red(f'ERROR: empty required field {fields[i]}, ') + yellow(f' -> Url: {url} '))
            logger.error("job.field_invalid", field=fields[i], url=url, debug=debugFlag)
        return False
    return True


def join(*str: str) -> str:
    return ''.join(str)


def removeUrlParameter(url: str, parameter: str) -> str:
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if parameter in qs:
        del qs[parameter]
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def summarize(keywords, totalResults, currentItem):
    printHR()
    logger.info("scraper.results_loaded", loaded=currentItem, total=totalResults, keywords=keywords,
                console=f'{getDatetimeNowStr()} - Loaded {currentItem} of {totalResults} total results for search: {keywords}')
    printHR()
    print()
