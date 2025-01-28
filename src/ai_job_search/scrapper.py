import sys
from ai_job_search.scrapper import indeed
import ai_job_search.scrapper.linkedin as linkedIn
import ai_job_search.scrapper.glassdoor as glassdoor
import ai_job_search.scrapper.infojobs as infojobs
from ai_job_search.tools.terminalColor import red, yellow


# FIXME: Implement scrapper by url in view and/or console
# f.ex.: https://www.glassdoor.es/Empleo/madrid-java-developer-empleos-SRCH_IL.0,6_IC2664239_KO7,21.htm?jl=1009607227015&srs=JV_APPLYPANE
# taking site id to check if already exists in db
# this could be an alternative way to add jobs in sites like glassdoor because of cloudflare security filter
# TODO: technoempleo scrapper
SCRAPPERS: dict = {'Linkedin': linkedIn,
                   'Infojobs': infojobs,
                   'Glassdoor': glassdoor,
                   'Indeed': indeed}

args = sys.argv
print('Scrapper init')
if len(args) == 1:
    # No arguments specified in command line
    print(f'Executing all scrappers: {SCRAPPERS.keys()}')
    for s in SCRAPPERS.values():
        s.run()
else:
    # Arguments specified in command line
    print(f'Executing specified scrappers: {args[1:]}')
    for arg in args[1:]:
        if SCRAPPERS.get(arg.capitalize()):
            SCRAPPERS.get(arg.capitalize()).run()
        else:
            print(red(f"Invalid scrapper web page name {arg}"))
            print(yellow(
                f"Available web page scrapper names: {SCRAPPERS.keys()}"))
