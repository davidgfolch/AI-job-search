import sys
from typing import Callable, Union, Optional

from commonlib.fileSystemUtil import getSrcPath
from commonlib.terminalColor import cyan, red, yellow
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.executor.executor_factory import process_page_url
from scrapper.core.scrapper_scheduler import ScrapperScheduler
from scrapper.core.scrapper_config import SCRAPPERS


def hasArgument(args: list, name: str, info: Callable[[], str] = lambda: "", expectedParamCount: Optional[int] = None) -> Optional[list]:
    if name not in args:
        return None
    index = args.index(name)
    count = expectedParamCount if expectedParamCount is not None else 0
    if index + 1 + count > len(args):
        print(red(f"Error: Missing arguments for '{name}'. Expected {count}."))
        sys.exit(1)
    extracted = args[index + 1 : index + 1 + count]
    del args[index : index + 1 + count]
    print(info())
    return extracted


def main(args):
    print(cyan('Scrapper init'))
    print(cyan('Usage: scrapper.py wait starting scrapperName'))
    print(cyan('wait -> waits for scrapper timeout before executing'))
    print(cyan('starting -> starts scrapping at the specified scrapper (by name)'))
    print(cyan('url -> scrapping only the specified url page'))

    wait = hasArgument(args, 'wait', lambda: "'wait' before execution", expectedParamCount=0)
    starting = hasArgument(args, 'starting', lambda: "'starting' mode enabled", expectedParamCount=1)
    url = hasArgument(args, 'url', lambda: "scrapping only url page", expectedParamCount=1)
    if url:
        process_page_url(url[0])
        return
    if starting:
        startingAt = starting[0].capitalize()
        if startingAt not in SCRAPPERS:
            print(red(f"Invalid scrapper web page name {startingAt}"))
            print(yellow(f"Available web page scrapper names: {list(SCRAPPERS.keys())}"))
            return
    else:
        startingAt = None

    with SeleniumService(debug=False) as seleniumUtil:
        persistenceManager = PersistenceManager()
        seleniumUtil.loadPage(f"file://{getSrcPath()}/scrapper/index.html")
        scheduler = ScrapperScheduler(persistenceManager, seleniumUtil)
        if len(args) == 1 or starting or wait:
            scheduler.runAllScrappers(wait is not None, starting is not None, startingAt)
        else:
            scheduler.runSpecifiedScrappers(args[1:])


if __name__ == '__main__':
    main(sys.argv)

