
import re
import traceback

# from bs4 import BeautifulSoup
# from markdownify import MarkdownConverter
import markdownify

from ai_job_search.tools.terminalColor import (
    blue, cyan, green, printHR, red, yellow)
from ai_job_search.tools.util import (
    AUTOMATIC_REPEATED_JOBS_MERGE, SHOW_SQL, hasLenAnyText, removeNewLines)
from ai_job_search.viewer.clean.mergeDuplicates import IDS_IDX, merge


def printScrapperTitle(scrapper: str):
    printHR(green)
    print(green(f'RUNNING {scrapper} scrapper'))
    printHR(green)


def printPage(webPage, page, totalPages, keywords):
    print(green(f'{webPage} Starting page {page} of {totalPages} ',
                f'search={keywords}'))
    printHR(green)


def htmlToMarkdown(html: str):
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
    # remove invalid scapes
    # TODO: REMOVE OR CHANGE UNICODE \u00f3
    md = md.replace('\$', '$')  # dont remove \$ ignore the warning
    md = re.sub(r'[\\]+(?!=a-z)', '', md, flags=re.M)
    return md


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


def mergeDuplicatedJobs(fncGetDuplicatedJobs):
    if not AUTOMATIC_REPEATED_JOBS_MERGE:
        return
    try:
        rows = fncGetDuplicatedJobs()
        if len(rows) == 0:
            return
        rows = [row[IDS_IDX] for row in rows]
        printHR(cyan)
        print(cyan('Merging duplicated jobs (into the last created one) ',
                   'and deleting older ones...'))
        printHR(cyan)
        for generatorResult in merge(rows):
            for line in generatorResult:
                if arr := line.get('arr', None):
                    print(cyan(*[removeNewLines(f'{a}') for a in arr]))
                if txt := line.get('query', None) and SHOW_SQL:
                    print(blue(removeNewLines(txt)))
                if txt := line.get('text', None):
                    print(blue(removeNewLines(txt)))
    except Exception:
        print(red(traceback.format_exc()))
