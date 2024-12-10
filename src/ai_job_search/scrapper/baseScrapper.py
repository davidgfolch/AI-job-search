
import re

# from bs4 import BeautifulSoup
# from markdownify import MarkdownConverter
import markdownify

from ai_job_search.tools.terminalColor import red, yellow


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
    return re.sub(r'(\s*(\n|\n\r|\r\n|\r)){2,}', '\n\n', html, re.M)


def validate(title: str, url: str, company: str, markdown: str,
             debugFlag: bool):
    if not (title.strip() and url and company and
            re.sub(r'\n', '', markdown, re.M).strip()):
        markdown = markdown.split('\n')[0]
        debug(debugFlag, "validate -> " +
              red('ERROR: One or more required fields are empty, ',
                  f'NOT inserting into DB: title={title}, company={company}, ',
                  f'markdown={markdown}...') +
              yellow(f' -> Url: {url}'))
        return False
    return True


def debug(debug: bool, msg: str = ''):
    if debug:
        input(f" (debug active) {msg}, press a key")
    else:
        print(msg, end='')


def join(*str: str) -> str:
    return ''.join(str)
