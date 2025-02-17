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
    'Linkedin': {
        'function': linkedin.run,
        'timer': '1h'},
    'Glassdoor': {
        'function': glassdoor.run,
        'timer': '3h'},
    'Infojobs': {
        'function': infojobs.run,
        'timer': '2h'},
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


def timeExpired():
    last = executionsTimes.get(name, None)
    if last:
        lapsed = getDatetimeNow()-last
        timeoutSeconds = getSeconds(properties['timer'])
        if lapsed + 1 <= timeoutSeconds:
            return False
    executionsTimes[name] = getDatetimeNow()
    return True


args = sys.argv
print('Scrapper init')
starting = 'starting' in args and len(args) == 3
startingAt = args[2].capitalize() if starting else None
print("'starting' in args ", 'starting' in args)
print("len(args) ", len(args))
if len(args) == 1 or starting:
    # No arguments specified in command line: run all
    # Specified params: starting glassdoor -> starts with glassdoor
    print(f'Executing all scrappers: {SCRAPPERS.keys()}')
    print(f'Starting at : {startingAt}')
    while True:
        for name, properties in SCRAPPERS.items():
            startAtThis = (starting and startingAt != name)
            if timeExpired():
                execFunction = properties['function']
                if properties.get('ignoreAutoRun', False) or startAtThis:
                    print(f'Skipping : {name}')
                    continue
                execFunction()
                starting = False
        consoleTimer(
            "Waiting for next scrapping execution trigger, ", '10m')
else:
    # Arguments specified in command line
    print(f'Executing specified scrappers: {args[1:]}')
    for arg in args[1:]:
        if SCRAPPERS.get(arg.capitalize()):
            SCRAPPERS.get(arg.capitalize())['function']()
        else:
            print(red(f"Invalid scrapper web page name {arg}"))
            print(yellow(
                f"Available web page scrapper names: {SCRAPPERS.keys()}"))
