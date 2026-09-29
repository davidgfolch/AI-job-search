import sys
from importlib.metadata import version as _v
from typing import Callable, Optional

from commonlib.observability import configure_logging, get_logger
from commonlib.sql.mysqlUtil import MysqlUtil, getConnection
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.executor.executor_factory import process_page_url
from scrapper.core.scrapper_scheduler import ScrapperScheduler
from scrapper.core.scrapper_config import SCRAPPERS

configure_logging("scrapper")
logger = get_logger("scrapper.main")

USAGE = (("wait", "waits for scrapper timeout before executing"),
         ("starting", "starts scrapping at the specified scrapper (by name)"),
         ("url", "scrapping only the specified url page"))


def hasArgument(args: list, name: str, info: Callable[[], str] = lambda: "", expectedParamCount: Optional[int] = None) -> Optional[list]:
    if name not in args:
        return None
    index = args.index(name)
    count = expectedParamCount if expectedParamCount is not None else 0
    if index + 1 + count > len(args):
        logger.error("cli.arguments_missing", argument=name, expected_count=count)
        sys.exit(1)
    extracted = args[index + 1 : index + 1 + count]
    del args[index : index + 1 + count]
    logger.debug("cli.argument_parsed", argument=name, value_count=count, detail=info())
    return extracted


def main(args):
    logger.info("cli.started", version=_v('scrapper'))
    logger.info("cli.initialised")
    logger.info("cli.usage", command="scrapper.py wait starting scrapperName")
    for mode, description in USAGE:
        logger.info("cli.usage", mode=mode, description=description)

    wait = hasArgument(args, 'wait', lambda: "'wait' before execution", expectedParamCount=0)
    starting = hasArgument(args, 'starting', lambda: "'starting' mode enabled", expectedParamCount=1)
    url = hasArgument(args, 'url', lambda: "scrapping only url page", expectedParamCount=1)
    if url:
        process_page_url(url[0])
        return
    if starting:
        startingAt = starting[0].capitalize()
        if startingAt not in SCRAPPERS:
            logger.error("cli.invalid_scrapper", scrapper=startingAt)
            logger.info("cli.available_scrappers", scrappers=list(SCRAPPERS.keys()))
            return
    else:
        startingAt = None

    with MysqlUtil(getConnection()) as mysql:
        scrapper_state_repository = mysql._scrapper_state_repository
    persistenceManager = PersistenceManager(
        repository=scrapper_state_repository
    )
    scheduler = ScrapperScheduler(persistenceManager)
    if len(args) == 1 or starting or wait:
        scheduler.runAllScrappers(wait is not None, starting is not None, startingAt)
    else:
        scheduler.runSpecifiedScrappers(args[1:])


if __name__ == '__main__':
    main(sys.argv)

