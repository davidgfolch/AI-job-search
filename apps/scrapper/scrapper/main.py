import sys
from typing import Callable

from commonlib.fileSystemUtil import getSrcPath
from commonlib.terminalColor import cyan
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.core.scrapper_execution import runScrapperPageUrl
from scrapper.core.scrapper_scheduler import ScrapperScheduler


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

    with SeleniumService() as seleniumUtil:
        persistenceManager = PersistenceManager()
        seleniumUtil.loadPage(f"file://{getSrcPath()}/scrapper/index.html")
        scheduler = ScrapperScheduler(persistenceManager, seleniumUtil)
        if len(args) == 1 or starting or wait:
            startingAt = args[1].capitalize() if starting else None
            scheduler.runAllScrappers(wait, starting, startingAt)
        else:
            scheduler.runSpecifiedScrappers(args[1:])


if __name__ == '__main__':
    main(sys.argv)

