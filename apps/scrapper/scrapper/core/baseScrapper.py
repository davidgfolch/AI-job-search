
import re
import traceback
from typing import Optional

from markdownify import MarkdownConverter
from commonlib.util import getEnv,getDatetimeNowStr, hasLenAnyText
from commonlib.terminalColor import green, printHR, red, yellow


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
    
def htmlToMarkdown(html: str) -> str:
    md = CustomConverter().convert(html)
    return removeInvalidScapes(md)


def removeInvalidScapes(md: str) -> str:
    md = md.replace('\$', '$')  # dont remove \$ ignore the warning
    # remove all backslash NOT unicode \uxxxx
    md = re.sub(r'\\(?!u[0-9a-fA-F]{4})', '', md, flags=re.M)
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


def debug(debugFlag: bool, msg: str = '', exception: Optional[bool]=None):
    exception = exception if exception is not None else debugFlag
    if debugFlag:
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
            print(red(msg))


def join(*str: str) -> str:
    return ''.join(str)
