
import re
import traceback

# from bs4 import BeautifulSoup
# from markdownify import MarkdownConverter
import markdownify


from ai_job_search.tools.terminalColor import green, printHR, red, yellow
from ai_job_search.tools.util import getDatetimeNowStr, getEnv, hasLenAnyText


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
    print("")
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


def htmlToMarkdown(html: str) -> str:
    # https://github.com/matthewwithanm/python-markdownify?tab=readme-ov-file#options
    # https://github.com/matthewwithanm/python-markdownify?tab=readme-ov-file#converting-beautifulsoup-objects
    # def convertSoup(soup, **options):
    #     return MarkdownConverter(**options).convert_soup(soup)

    # html = BeautifulSoup(html)  # exclude_encodings
    # md = convertSoup(html)
    # print(yellow('>>> Markdown with previous beautifulSoup clean <<<'))
    # print(green(md))
    md = markdownify.markdownify(html)
    return removeInvalidScapes(md)


def removeInvalidScapes(md: str) -> str:
    md = md.replace('\$', '$')  # dont remove \$ ignore the warning
    # remove all backslash NOT unicode \uxxxx
    md = re.sub(r'[\\]+(?!=u)', '', md, flags=re.M)
    return md


def removeLinks(md: str) -> str:
    # remove all links, but keep the text
    return re.sub(r'\[([^\]]+)\]\([^\)]+\)', r' \1 ', md, flags=re.M)


def validate(title: str, url: str, company: str, markdown: str,
             debugFlag: bool):
    fields = ['title', 'url', 'company', 'markdown']
    validations = hasLenAnyText(title, url, company, markdown)
    if 0 in validations:
        for i, v in enumerate(validations):
            debug(debugFlag, "validate -> " +
                  red(f'ERROR: empty required field {fields[i]}, ') +
                  yellow(f' -> Url: {url} '))
        return False
    return True


def debug(debug: bool, msg: str = '', exception=False):
    if debug:
        msg = f" (debug active) {msg}, press a key"
        if exception:
            print(yellow(msg))
            input(red(traceback.format_exc()))
        else:
            input(red(msg))
    else:
        if exception:
            print(yellow(msg))
            print(red(traceback.format_exc()))
        else:
            print(red(msg), end='')


def join(*str: str) -> str:
    return ''.join(str)
