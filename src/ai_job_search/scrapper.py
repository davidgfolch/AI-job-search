import sys
from ai_job_search.scrapper import (
    linkedin, indeed, infojobs, glassdoor, tecnoempleo)
from ai_job_search.tools.terminalColor import red, yellow
from ai_job_search.tools.util import consoleTimer, getDatetimeNow, getSeconds

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
    'Linkedin': {
        'function': linkedin.run,
        'timer': '1h'},
    'Glassdoor': {
        'function': glassdoor.run,
        'timer': '3h'},
    'Tecnoempleo': {
        'function': tecnoempleo.run,
        'timer': '2h'},
    'Indeed': {
        'function': indeed.run,
        'timer': '3h',
        'ignoreAutoRun': True
    },
}
executionsTimes = {}


def timeExpired(name: str, timeout: int, waitBeforeFirstRuns: bool):
    defaultLast = getDatetimeNow() if waitBeforeFirstRuns else None
    last = executionsTimes.get(name, defaultLast)
    if last:
        lapsed = getDatetimeNow()-last
        timeoutSeconds = getSeconds(timeout)
        if lapsed + 1 <= timeoutSeconds:
            return False
    executionsTimes[name] = getDatetimeNow()
    return True


def runAllScrappers(waitBeforeFirstRuns, starting):
    # No arguments specified in command line: run all
    # Specified params: starting glassdoor -> starts with glassdoor
    print(f'Executing all scrappers: {SCRAPPERS.keys()}')
    startingAt = args[1].capitalize() if starting else None
    print(f'Starting at : {startingAt}')
    while True:
        for name, properties in SCRAPPERS.items():
            if timeExpired(name, properties['timer'], waitBeforeFirstRuns):
                notStartAtThisOne = (starting and startingAt != name)
                if properties.get('ignoreAutoRun', False) or notStartAtThisOne:
                    print(f'Skipping : {name}')
                    continue
                properties['function']()
                starting = False
        waitBeforeFirstRuns = False
        consoleTimer(
            "Waiting for next scrapping execution trigger, ", '10m')


def runSpecifiedScrappers():
    # Arguments specified in command line
    print(f'Executing specified scrappers: {args[1:]}')
    for arg in args[1:]:
        if SCRAPPERS.get(arg.capitalize()):
            SCRAPPERS.get(arg.capitalize())['function']()
        else:
            print(red(f"Invalid scrapper web page name {arg}"))
            print(yellow(
                f"Available web page scrapper names: {SCRAPPERS.keys()}"))


args = sys.argv
print('Scrapper init')
print('Usage: scrapper.py wait starting scrapperName')
print('wait -> waits for scrapper timeout before executing')
print('starting -> starts scrapping at the specified scrapper (by name)')

starting = 'starting' in args
if starting:
    args.pop(args.index('starting'))
    print(f"'starting' at {args[1]} ")
wait = 'wait' in args
if wait:
    args.pop(args.index('wait'))
    print("'wait' before execution", )

if len(args) == 1 or starting or wait:
    runAllScrappers(wait, starting)
else:
    runSpecifiedScrappers()
