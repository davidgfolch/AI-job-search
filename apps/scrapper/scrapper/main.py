import sys
from typing import Callable

from commonlib.util import getSrcPath
from commonlib.terminalColor import cyan
from scrapper.seleniumUtil import SeleniumUtil
from scrapper.persistence_manager import PersistenceManager
from scrapper.container.scrapper_container import ScrapperContainer

from scrapper.scrapper_execution import runScrapperPageUrl
from scrapper.scrapper_scheduler import runAllScrappers, runSpecifiedScrappers


def hasArgument(args: list, name: str, info: Callable = (lambda: str)) -> bool:
    exists = name in args
    if exists:
        args.pop(args.index(name))
        print(info())
    return exists


def main(args):
    print(cyan('Scrapper init'))
    print(cyan('Usage: scrapper.py wait starting scrapperName'))
    print(cyan('wait -> waits for scrapper timeout before executing'))
    print(cyan('starting -> starts scrapping at the specified scrapper (by name)'))
    print(cyan('url -> scrapping only the specified url page'))

    wait = hasArgument(args, 'wait', lambda: "'wait' before execution")
    starting = hasArgument(args, 'starting', lambda: f"'starting' at {args[1]} ")
    url = hasArgument(args, 'url', lambda: f"scrapping only url page -> {args[1]} ")

    if len(args) == 2 and url:
        runScrapperPageUrl(args[1])
        return

    with SeleniumUtil() as seleniumUtil:
        persistenceManager = PersistenceManager()
        scrapperContainer = ScrapperContainer()
        seleniumUtil.loadPage(f"file://{getSrcPath()}/scrapper/index.html")
        if len(args) == 1 or starting or wait:
            startingAt = args[1].capitalize() if starting else None
            runAllScrappers(wait, starting, startingAt, persistenceManager, seleniumUtil, scrapperContainer)
        else:
            runSpecifiedScrappers(args[1:], persistenceManager, seleniumUtil, scrapperContainer)


if __name__ == '__main__':
    main(sys.argv)

