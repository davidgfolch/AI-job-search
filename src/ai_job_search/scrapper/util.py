import os
from dotenv import load_dotenv
from ai_job_search.tools.terminalColor import yellow

load_dotenv()


def getAndCheckEnvVars(site: str):
    mail = os.environ.get(f'{site}_EMAIL')
    pwd = os.environ.get(f'{site}_PWD')
    search = os.environ.get(f'{site}_JOBS_SEARCH')
    if not search:
        search = os.environ.get('JOBS_SEARCH')
    if not mail or not pwd or not search:
        print(yellow('Set up .venv file with the following keys:'))
        print(yellow(f'{site}_EMAIL' if not mail else '',
                     f'{site}_PWD' if not pwd else '',
                     f'{site}_JOBS_SEARCH' if not search else ''))
        print(yellow('Please read README.md for more info'))
        exit()
    return mail, pwd, search


def getEnv(key: str):
    return os.environ.get(key)
