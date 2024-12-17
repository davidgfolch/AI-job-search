import sys
from ai_job_search.scrapper.seleniumUtil import SeleniumUtil
import ai_job_search.scrapper.linkedin as linkedIn
import ai_job_search.scrapper.glassdoor as glassdoor
import ai_job_search.scrapper.infojobs as infojobs
from ai_job_search.tools.terminalColor import red, yellow

SCRAPPERS = ['LinkedIn', 'Glassdoor', 'Infojobs']

args = sys.argv
print('Scrapper init')
if len(args) == 1:
    # No arguments specified in command line
    print(f'Executing all scrappers: {SCRAPPERS}')
    seleniumUtil = SeleniumUtil()
    linkedIn.run(seleniumUtil)
    seleniumUtil.close()
    infojobs.run()
    glassdoor.run()
else:
    # Arguments specified in command line
    print(f'Executing specified scrappers: {args}')
    for arg in args[1:]:
        match arg.lower():
            case 'linkedin':
                seleniumUtil = SeleniumUtil()
                linkedIn.run(seleniumUtil)
                seleniumUtil.close()
            case 'glassdoor':
                glassdoor.run()
            case 'infojobs':
                infojobs.run()
            case _:
                print(red(f"Invalid scrapper web page name {arg}"))
                print(
                    yellow(f"Available web page scrapper names: {SCRAPPERS}"))
