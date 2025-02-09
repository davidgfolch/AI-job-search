import datetime
import random
import re
from time import sleep
from ai_job_search.tools.terminalColor import yellow
import os
from typing import Iterator
from dotenv import load_dotenv

load_dotenv()


def getAndCheckEnvVars(site: str):
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
    return txt.replace('\n', ' ').replace('\r', '')


SHOW_SQL = toBool(getEnv('SHOW_SQL', True))
AUTOMATIC_REPEATED_JOBS_MERGE = toBool(
    getEnv('AUTOMATIC_REPEATED_JOBS_MERGE', True))
print(f"SHOW_SQL={SHOW_SQL} {type(SHOW_SQL)}")
print(f'AUTOMATIC_REPEATED_JOBS_MERGE={AUTOMATIC_REPEATED_JOBS_MERGE}',
      f' {type(AUTOMATIC_REPEATED_JOBS_MERGE)}')


def consoleTimer(message: str, timeUnit: str):
    """timeUnit: 30s|8m|2h"""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600}
    unit = timeUnit[-1]
    seconds = int(timeUnit[:-1]) * seconds_per_unit[unit]
    # TODO: spinner abstraction
    spinners = ["←↖↑↗→↘↓↙", "▁▃▄▅▆▇█▇▆▅▄▃", "▉▊▋▌▍▎▏▎▍▌▋▊▉", "▖▘▝▗",
                "▌▀▐▄", "┤┘┴└├┌┬┐", "◢◣◤◥", "◰◳◲◱", "◴◷◶◵", "◐◓◑◒",
                "|/-\\", ".oO@*", "◇◈◆", "⣾⣽⣻⢿⡿⣟⣯⣷",
                "⡀⡁⡂⡃⡄⡅⡆⡇⡈⡉⡊⡋⡌⡍⡎⡏⡐⡑⡒⡓⡔⡕⡖⡗⡘⡙⡚⡛⡜⡝⡞⡟⡠⡡⡢⡣⡤⡥⡦⡧⡨⡩⡪⡫⡬⡭⡮⡯⡰⡱⡲⡳⡴⡵⡶⡷⡸⡹⡺⡻⡼⡽⡾⡿⢀⢁⢂⢃⢄⢅⢆⢇⢈⢉⢊⢋⢌⢍⢎⢏⢐⢑⢒⢓⢔⢕⢖⢗⢘⢙⢚⢛⢜⢝⢞⢟⢠⢡⢢⢣⢤⢥⢦⢧⢨⢩⢪⢫⢬⢭⢮⢯⢰⢱⢲⢳⢴⢵⢶⢷⢸⢹⢺⢻⢼⢽⢾⢿⣀⣁⣂⣃⣄⣅⣆⣇⣈⣉⣊⣋⣌⣍⣎⣏⣐⣑⣒⣓⣔⣕⣖⣗⣘⣙⣚⣛⣜⣝⣞⣟⣠⣡⣢⣣⣤⣥⣦⣧⣨⣩⣪⣫⣬⣭⣮⣯⣰⣱⣲⣳⣴⣵⣶⣷⣸⣹⣺⣻⣼⣽⣾⣿", "⠁⠂⠄⡀⢀⠠⠐⠈"]
    spin = spinners[random.randint(0, len(spinners)-1)]
    tickXSec = 6
    spinItem = 0
    for left in range(seconds*tickXSec, 0, -1):
        spinX = spin[spinItem]*5
        count = str(datetime.timedelta(seconds=int(left/tickXSec)))
        print(yellow(
            message,
            f"{spinX} I'll retry in {count} {spinX}",
            f"{' '*10}"),
            end='\r')
        spinItem = spinItem+1 if spinItem+1 < len(spin) else 0
        sleep(1/tickXSec)
