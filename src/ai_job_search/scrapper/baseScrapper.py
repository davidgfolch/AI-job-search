
from functools import reduce
import re
import traceback

# from bs4 import BeautifulSoup
# from markdownify import MarkdownConverter
import markdownify

from ai_job_search.tools.terminalColor import green, red, yellow


def printScrapperTitle(scrapper: str):
    printHR(green)
    print(green(f'RUNNING {scrapper} scrapper'))
    printHR(green)


def printPage(webPage, page, totalPages, keywords):
    print(green(f'{webPage} Starting page {page} of {totalPages} ',
                f'search={keywords}'))
    printHR(green)


def printHR(colorFnc=None):
    if colorFnc:
        print(colorFnc('-'*150))
    else:
        print('-'*150)


def htmlToMarkdown(html: str):
    # https://github.com/matthewwithanm/python-markdownify?tab=readme-ov-file#options
    # https://github.com/matthewwithanm/python-markdownify?tab=readme-ov-file#converting-beautifulsoup-objects
    # def convertSoup(soup, **options):
    #     return MarkdownConverter(**options).convert_soup(soup)

    # html = BeautifulSoup(html)  # exclude_encodings
    # md = convertSoup(html)
    # print(yellow('>>> Markdown with previous beautifulSoup clean <<<'))
    # print(green(md))
    return removeBlankLines(markdownify.markdownify(html))


def removeBlankLines(html: str):
    return re.sub(r'(\s*)(\n|\n\r|\r\n)+(\n|\n\r|\r\n)+', r'\1\n\n',
                  html, re.M)


def validate(title: str, url: str, company: str, markdown: str,
             debugFlag: bool):
    if not hasLen(title, url, company, markdown):
        debug(debugFlag, "validate -> " +
              red('ERROR: One or more required fields are empty, ',
                  f'NOT inserting into DB: title={title}, company={company}, ',
                  f'markdown={markdown}...') +
              yellow(f' -> Url: {url}'))
        return False
    return True


def hasLen(*texts: str):
    return reduce(lambda a, b: a and b,
                  [t and len(removeBlanks(t)) > 0 for t in texts])


def removeBlanks(text):
    return re.sub(r'[\n\b]+', '', text, re.M).strip()


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
