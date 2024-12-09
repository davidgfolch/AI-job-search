import os
from dotenv import load_dotenv
from ai_job_search.tools.terminalColor import yellow

load_dotenv()


def getAndCheckEnvVars(site: str):
    mail = os.environ.get(f'{site}_EMAIL')
    pwd = os.environ.get(f'{site}_PWD')
    search = os.environ.get(f'{site}_JOBS_SEARCH')
    if not mail or not pwd or not search:
        print(yellow('Please read README.md first'))
        print(yellow('Set up .venv file with email pwd & search params.'))
        exit()
    return mail, pwd, search
