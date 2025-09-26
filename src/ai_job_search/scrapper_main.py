import sys
import traceback
from ai_job_search.scrapper import (
    linkedin, indeed, infojobs, glassdoor, tecnoempleo)
from ai_job_search.scrapper.seleniumUtil import SeleniumUtil
from ai_job_search.tools.terminalColor import cyan, red, yellow
from ai_job_search.tools.util import consoleTimer, getDatetimeNow, getSeconds, getTimeUnits

# FIXME: Implement scrapper by url in view and/or console
# f.ex.: https://www.glassdoor.es/Empleo/madrid-java-developer-empleos-
# SRCH_IL.0,6_IC2664239_KO7,21.htm?jl=1009607227015&srs=JV_APPLYPANE
# taking site id to check if already exists in db
# this could be an alternative way to add jobs in sites like glassdoor because
# of cloudflare security filter
SCRAPPERS: dict = {
    'Infojobs': {  # first to solve security filter
        'function': infojobs.run,
        'timer': '2h'},
    'Tecnoempleo': { # first to solve security filter
        'function': tecnoempleo.run,
        'timer': '2h'},
    'Linkedin': {
        'function': linkedin.run,
        'timer': '1h'},
    'Glassdoor': {
        'function': glassdoor.run,
        'timer': '3h'},
    'Indeed': {
        'function': indeed.run,
        'timer': '3h',
        'ignoreAutoRun': True
    },
}
MAX_NAME = max([len(k) for k in SCRAPPERS.keys()])
executionsTimes = {}
seleniumUtil: SeleniumUtil = None


def timeExpired(name: str, properties: dict):
    executionsTimes[name] = executionsTimes.get(name, getDatetimeNow() if properties['waitBeforeFirstRun'] else None)
    if last := executionsTimes[name]:
        lapsed = getDatetimeNow()-last
        timeoutSeconds = getSeconds(properties['timer'])
        timeLeft = getTimeUnits(timeoutSeconds-lapsed)
        print(f'Executing {name.rjust(MAX_NAME)} in {timeLeft.rjust(11)}')
        if lapsed + 1 <= timeoutSeconds:
            return False
    executionsTimes[name] = getDatetimeNow()
    return True


def runAllScrappers(waitBeforeFirstRuns, starting, startingAt, loop=True):
    # No arguments specified in command line: run all
    # Specified params: starting glassdoor -> starts with glassdoor
    print(f'Executing all scrappers: {SCRAPPERS.keys()}')
    print(f'Starting at : {startingAt}')
    for name, properties in SCRAPPERS.items():
        print(yellow(f'\nPRELOADING {name}: login & security filters'))
        seleniumUtil.tab(name)
        properties['function'](seleniumUtil, True)
    while True:
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
            seleniumUtil.tab(runThis['name'])
            executeScrapper(runThis['name'], runThis['properties'])
        waitBeforeFirstRuns = False
        consoleTimer("Waiting for next scrapping execution trigger, ", '10m')
        if not loop:
            break


def runSpecifiedScrappers(scrappersList: list):
    # Arguments specified in command line
    print(f'Executing specified scrappers: {scrappersList}')
    for arg in scrappersList:
        print(yellow(f'\nPRELOADING {arg}: login & security filters'))
        seleniumUtil.tab(arg)
        properties = SCRAPPERS[arg.capitalize()]
        properties['function'](seleniumUtil, True)
    for arg in scrappersList:
        if SCRAPPERS.get(arg.capitalize()):
            properties = SCRAPPERS[arg.capitalize()]
            executeScrapper(arg.capitalize(), properties)
        else:
            print(red(f"Invalid scrapper web page name {arg}"))
            print(yellow(f"Available web page scrapper names: {SCRAPPERS.keys()}"))


def executeScrapper(name, properties: dict):
    try:
        properties['function'](seleniumUtil, False)
    except Exception as e:
        print(red(f"Error occurred while executing {name}: {e}"))
        print(red(traceback.format_exc()))
        executionsTimes[name] = getSeconds(properties['timer']) # re-execute resetting timer


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
        if len(args) == 1 or starting or wait:
            startingAt = args[1].capitalize() if starting else None
            runAllScrappers(wait, starting, startingAt)
        else:
            runSpecifiedScrappers(args[1:])
