import sys
import traceback

from commonlib.util import getDatetimeNow, getEnv, getEnvBool, getSeconds, getTimeUnits, getSrcPath, consoleTimer
from commonlib.terminalColor import cyan, red, yellow, green
from scrapper.seleniumUtil import SeleniumUtil
from scrapper import tecnoempleo, infojobs, linkedin, glassdoor, indeed

# Try to import new SOLID architecture
try:
    from scrapper.container.scrapper_container import ScrapperContainer
    from scrapper.services.scrapping_service import ScrappingService
    NEW_ARCHITECTURE_AVAILABLE = True
except ImportError:
    NEW_ARCHITECTURE_AVAILABLE = False
    ScrapperContainer = None
    ScrappingService = None

# FIXME: Implement scrapper by url in view and/or console
# f.ex.: https://www.glassdoor.es/Empleo/madrid-java-developer-empleos-
# SRCH_IL.0,6_IC2664239_KO7,21.htm?jl=1009607227015&srs=JV_APPLYPANE
# taking site id to check if already exists in db
# this could be an alternative way to add jobs in sites like glassdoor because
# of cloudflare security filter
SCRAPPERS: dict = {
    'Infojobs': {  # first to solve security filter
        'function': infojobs.run,
        'timer': getSeconds(getEnv('INFOJOBS_RUN_CADENCY'))},
    'Tecnoempleo': { # first to solve security filter
        'function': tecnoempleo.run,
        'timer': getSeconds(getEnv('TECNOEMPLEO_RUN_CADENCY'))},
    'Linkedin': {
        'function': linkedin.run,
        'timer': getSeconds(getEnv('LINKEDIN_RUN_CADENCY')),
        'closeTab': True},
    'Glassdoor': {
        'function': glassdoor.run,
        'timer': getSeconds(getEnv('GLASSDOOR_RUN_CADENCY'))},
    'Indeed': {
        'function': indeed.run,
        'timer': getSeconds(getEnv('INDEED_RUN_CADENCY')),
        'ignoreAutoRun': True
    },
}
print(f'Scrappers config: {SCRAPPERS}')
RUN_IN_TABS=getEnvBool('RUN_IN_TABS', False)
NEXT_SCRAP_TIMER = '10m'  # '10m'  # time to wait between scrapping executions
MAX_NAME = max([len(k) for k in SCRAPPERS.keys()])

seleniumUtil: SeleniumUtil = None


def timeExpired(name: str, properties: dict):
    defaultLastExecution = getDatetimeNow() if properties['waitBeforeFirstRun'] else None
    properties['lastExecution'] = properties.get('lastExecution', defaultLastExecution)
    if last := properties['lastExecution']:
        if last is None:
            return True
        lapsed = getDatetimeNow()-last
        timeoutSeconds = properties['timer']
        timeLeft = getTimeUnits(timeoutSeconds-lapsed)
        print(f'Executing {name.rjust(MAX_NAME)} in {timeLeft.rjust(11)}')
        if lapsed + 1 <= timeoutSeconds:
            return False
    properties['lastExecution'] = getDatetimeNow()
    return True


def runAllScrappers(waitBeforeFirstRuns, starting, startingAt, loops=99999999999):
    # No arguments specified in command line: run all
    # Specified params: starting glassdoor -> starts with glassdoor
    print(f'Executing all scrappers: {SCRAPPERS.keys()}')
    print(f'Starting at : {startingAt}')
    # for name, properties in SCRAPPERS.items():  THIS CAUSES PROBLEMS WITH URL LIB SOCKET DISCONNECTION & PROCESS HANGS LONG TIME.
    #     executeScrapperPreload(name, properties)
    count = 0
    while loops==99999999999 or count<loops:
        count += 1
        toRun = []
        for name, properties in SCRAPPERS.items():
            properties['waitBeforeFirstRun'] = properties.get('waitBeforeFirstRun', waitBeforeFirstRuns)
            if timeExpired(name, properties):
                notStartAtThisOne = (starting and startingAt != name)
                if properties.get('ignoreAutoRun', False) or notStartAtThisOne:
                    print(f'Skipping : {name}')
                    continue
                properties['waitBeforeFirstRun'] = False
                toRun.append({"name": name, "properties": properties})
                starting = False
        for runThis in toRun:
            if RUN_IN_TABS:
                seleniumUtil.tab(runThis['name'])
            if runPreload(runThis['properties']):
                executeScrapperPreload(runThis['name'], runThis['properties'])
            executeScrapper(runThis['name'], runThis['properties'])
        waitBeforeFirstRuns = False
        consoleTimer("Waiting for next scrapping execution trigger, ", NEXT_SCRAP_TIMER)


def runSpecifiedScrappers(scrappersList: list):
    # Arguments specified in command line
    print(f'Executing specified scrappers: {scrappersList}')
    # for arg in scrappersList:
    #     if validScrapperName(arg):
    #         properties = SCRAPPERS[arg.capitalize()]
    #         executeScrapperPreload(arg.capitalize(), properties)
    for arg in scrappersList:
        if validScrapperName(arg):            
            properties = SCRAPPERS[arg.capitalize()]
            if runPreload(properties):
                executeScrapperPreload(arg.capitalize(), properties)
            executeScrapper(arg.capitalize(), properties)

def runPreload(properties: dict) -> bool:
    if seleniumUtil.useUndetected:
        return False
    return not properties.get('preloaded',False) or properties.get('closeTab',False) or not RUN_IN_TABS


def validScrapperName(name: str):
    if SCRAPPERS.get(name.capitalize()) is not None:
        return True
    print(red(f"Invalid scrapper web page name {name}"))
    print(yellow(f"Available web page scrapper names: {SCRAPPERS.keys()}"))
    return False


def executeScrapperPreload(name, properties: dict):
    try:
        if RUN_IN_TABS:
            seleniumUtil.tab(name)
        # Try new architecture first for supported scrappers
        if NEW_ARCHITECTURE_AVAILABLE and name.lower() == 'linkedin':
            executeScrapperPreloadNewArchitecture(name, properties)
        else:
            # Fallback to old architecture
            properties['function'](seleniumUtil, True)
        properties['preloaded'] = True
    except Exception as e:
        print(red(f"Error occurred while preloading {name}: {e}"))
        print(red(traceback.format_exc()))
        properties['preloaded'] = False


def executeScrapperPreloadNewArchitecture(name: str, properties: dict):
    """Execute scrapper preload using new SOLID architecture"""
    try:
        container = ScrapperContainer()
        scrapping_service = container.get_scrapping_service(name.lower())
        
        # Execute preload (login only)
        results = scrapping_service.execute_scrapping(seleniumUtil, [], preload_only=True)
        
        if results.get('login_success', False):
            print(green(f"Preload completed successfully for {name}"))
        else:
            print(red(f"Preload failed for {name}"))
            raise Exception("Login failed")
        
    except Exception as e:
        print(red(f"Error in new architecture preload for {name}: {e}"))
        # Fallback to old method
        properties['function'](seleniumUtil, True)


def executeScrapper(name, properties: dict):        
    try:
        # Try new architecture first for supported scrappers
        if NEW_ARCHITECTURE_AVAILABLE and name.lower() == 'linkedin':
            executeScrapperNewArchitecture(name, properties)
        else:
            # Fallback to old architecture
            properties['function'](seleniumUtil, False)
    except Exception as e:
        print(red(f"Error occurred while executing {name}: {e}"))
        print(red(traceback.format_exc()))
        properties['lastExecution'] = None  # re-execute resetting timer
    except KeyboardInterrupt:
        pass
    finally:
        if RUN_IN_TABS:
            if properties.get('closeTab',False):
                seleniumUtil.tabClose(name)
            seleniumUtil.tab()  # switches to default tab


def executeScrapperNewArchitecture(name: str, properties: dict):
    """Execute scrapper using new SOLID architecture"""
    try:
        container = ScrapperContainer()
        scrapping_service = container.get_scrapping_service(name.lower())
        
        # Get keywords from environment
        keywords_list = getEnv('LINKEDIN_JOBS_SEARCH', getEnv('JOBS_SEARCH', '')).split(',')
        
        # Execute scrapping
        results = scrapping_service.execute_scrapping(seleniumUtil, keywords_list, preload_only=False)
        
        # Print results
        print(green(f"Scrapping completed for {name}:"))
        print(f"  Processed: {results['total_processed']} jobs")
        print(f"  Saved: {results['total_saved']} jobs")
        print(f"  Duplicates: {results['total_duplicates']} jobs")
        if results['errors']:
            print(red(f"  Errors: {len(results['errors'])}"))
            for error in results['errors'][:3]:  # Show first 3 errors
                print(red(f"    - {error}"))
        
    except Exception as e:
        print(red(f"Error in new architecture for {name}: {e}"))
        # Fallback to old method
        properties['function'](seleniumUtil, False)


if __name__ == '__main__':
    args = sys.argv
    print(cyan('Scrapper init'))
    print(cyan('Usage: scrapper.py wait starting scrapperName'))
    print(cyan('wait -> waits for scrapper timeout before executing'))
    print(cyan('starting -> starts scrapping at the specified scrapper (by name)'))

    wait = 'wait' in args
    if wait:
        args.pop(args.index('wait'))
        print("'wait' before execution", )
    starting = 'starting' in args
    if starting:
        args.pop(args.index('starting'))
        print(f"'starting' at {args[1]} ")

    with SeleniumUtil() as seleniumUtil:
        seleniumUtil.loadPage(f"file://{getSrcPath()}/scrapper/index.html")
        if len(args) == 1 or starting or wait:
            startingAt = args[1].capitalize() if starting else None
            runAllScrappers(wait, starting, startingAt)
        else:
            runSpecifiedScrappers(args[1:])
