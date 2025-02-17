from datetime import datetime, timedelta
import random
import re
from time import sleep
from ai_job_search.tools.terminalColor import yellow
import os
from typing import Iterator
from dotenv import load_dotenv


def getEnvModified() -> float | None:
    return os.stat('.env').st_ctime if os.stat('.env') else None


load_dotenv()
envLastModified = getEnvModified()


def checkEnvReload():
    global envLastModified
    if envLastModified == getEnvModified():
        return
    print(yellow('Reloading .env'))
    load_dotenv()
    envLastModified == getEnvModified()


def getAndCheckEnvVars(site: str):
    checkEnvReload()
    mail = getEnv(f'{site}_EMAIL')
    pwd = getEnv(f'{site}_PWD')
    search = getEnv(f'{site}_JOBS_SEARCH')
    if not search:
        search = getEnv('JOBS_SEARCH')
    if not mail or not pwd or not search:
        print(yellow('Set up .venv file with the following keys:'))
        print(yellow(f'{site}_EMAIL' if not mail else '',
                     f'{site}_PWD' if not pwd else '',
                     f'{site}_JOBS_SEARCH' if not search else ''))
        print(yellow('Please read README.md for more info'))
        exit()
    return mail, pwd, search


def getEnv(key: str, default=None):
    checkEnvReload()
    return os.environ.get(key, default)


def hasLen(iter: Iterator):
    return any(True for _ in iter)


def hasLenAnyText(*texts: str) -> list[bool]:
    return [t is not None and len(removeBlanks(t)) > 0 for t in texts]


def removeBlanks(text):
    return re.sub(r'[\n\b]+', '', text, re.M).strip()


def toBool(str: str) -> bool:
    if str is None:
        return False
    return str.lower() in ['true', '1', 'yes']


def removeExtraEmptyLines(txt: str) -> str:
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'\s+\n', '\n', txt))


def removeNewLines(txt: str) -> str:
    try:
        return txt.replace('\n', ' ').replace('\r', '')
    except Exception:
        return str(txt)


SHOW_SQL = toBool(getEnv('SHOW_SQL', True))
AUTOMATIC_REPEATED_JOBS_MERGE = toBool(
    getEnv('AUTOMATIC_REPEATED_JOBS_MERGE', True))
print(f"SHOW_SQL={SHOW_SQL} {type(SHOW_SQL)}")
print(f'AUTOMATIC_REPEATED_JOBS_MERGE={AUTOMATIC_REPEATED_JOBS_MERGE}',
      f' {type(AUTOMATIC_REPEATED_JOBS_MERGE)}')
AI_ENRICHMENT_JOB_TIMEOUT_MINUTES = getEnv(
    'AI_ENRICHMENT_JOB_TIMEOUT_MINUTES', 5)


def consoleTimer(message: str, timeUnit: str):
    """timeUnit: 30s|8m|2h"""
    seconds = getSeconds(timeUnit)
    spinner = Spinner()
    try:
        for left in range(seconds*spinner.tickXSec, 0, -1):
            spinnerStr = spinner.generate()
            timeLeft = str(timedelta(
                seconds=int(left/spinner.tickXSec)))
            print(yellow(message,
                         f"{spinnerStr} I'll retry in {timeLeft} {spinnerStr}",
                         f"{' '*10}"),
                  end='\r')
            spinner.nextTick()
            sleep(1/spinner.tickXSec)
    finally:
        print()


def getSeconds(timeUnit: str):
    """timeUnit: 30s|8m|2h"""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600}
    unit = timeUnit[-1]
    seconds = int(timeUnit[:-1]) * seconds_per_unit[unit]
    return seconds


def getDatetimeNow() -> int:
    return int(datetime.now().timestamp())


class Spinner():
    SPINNERS = [
        "←↖↑↗→↘↓↙", "▁▃▄▅▆▇█▇▆▅▄▃", "▉▊▋▌▍▎▏▎▍▌▋▊▉", "▖▘▝▗",
        "▌▀▐▄", "┤┘┴└├┌┬┐", "◢◣◤◥", "◰◳◲◱", "◴◷◶◵", "◐◓◑◒",
        "|/-\\", ".oO@*", "◇◈◆", "⣾⣽⣻⢿⡿⣟⣯⣷",
        "⡀⡁⡂⡃⡄⡅⡆⡇⡈⡉⡊⡋⡌⡍⡎⡏⡐⡑⡒⡓⡔⡕⡖⡗⡘⡙⡚⡛⡜⡝⡞⡟⡠⡡⡢⡣⡤⡥⡦⡧⡨⡩⡪⡫⡬⡭⡮⡯⡰⡱⡲⡳⡴⡵⡶⡷⡸⡹⡺⡻⡼⡽⡾⡿⢀⢁⢂" +
        "⢃⢄⢅⢆⢇⢈⢉⢊⢋⢌⢍⢎⢏⢐⢑⢒⢓⢔⢕⢖⢗⢘⢙⢚⢛⢜⢝⢞⢟⢠⢡⢢⢣⢤⢥⢦⢧⢨⢩⢪⢫⢬⢭⢮⢯⢰⢱⢲⢳⢴⢵⢶⢷⢸⢹⢺⢻⢼⢽⢾⢿⣀⣁⣂⣃⣄⣅" +
        "⣆⣇⣈⣉⣊⣋⣌⣍⣎⣏⣐⣑⣒⣓⣔⣕⣖⣗⣘⣙⣚⣛⣜⣝⣞⣟⣠⣡⣢⣣⣤⣥⣦⣧⣨⣩⣪⣫⣬⣭⣮⣯⣰⣱⣲⣳⣴⣵⣶⣷⣸⣹⣺⣻⣼⣽⣾⣿", "⠁⠂⠄⡀⢀" +
        "⠠⠐⠈"]
    tickXSec = 6
    spinItem = 0
    spinner = None

    def __init__(self):
        self.spinner = self.SPINNERS[random.randint(0, len(self.SPINNERS)-1)]

    def nextTick(self):
        self.spinItem = self.spinItem + \
            1 if self.spinItem+1 < len(self.spinner) else 0

    def generate(self):
        return self.spinner[self.spinItem]*5
