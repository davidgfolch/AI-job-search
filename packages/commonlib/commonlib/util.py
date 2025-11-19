from pathlib import Path
from os.path import isfile, join
from datetime import datetime, timedelta
import random
import re
from time import sleep
import os
from typing import Iterator
from dotenv import load_dotenv
from .terminalColor import yellow


def getEnvModified() -> float | None:
    x = os.stat('../../.env').st_ctime if os.stat('../../.env') else None
    return x


load_dotenv()
envLastModified = getEnvModified()


def checkEnvReload():
    global envLastModified
    modified = envLastModified == getEnvModified()
    if modified:
        return
    print(yellow('Reloading .env'))
    load_dotenv(override=True)
    envLastModified = getEnvModified()


def getEnv(key: str, default: str = None) -> str:
    checkEnvReload()
    v = os.environ.get(key, default)
    return v


def getEnvMultiline(key: str, default: str = None) -> str:
    idx = 1
    value = ''
    while True:
        partialValue = getEnv(f'{key}_{idx}')
        if partialValue is None:
            break
        value += partialValue
        idx += 1
    return value


def getEnvBool(key: str, default: bool = False) -> bool:
    v = getEnv(key, str(default) if default else None)
    if v is None:
        return default
    return v.lower() == "true"


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


def consoleTimer(message: str, timeUnit: str, end='\r'):
    """timeUnit: 30s|8m|2h"""
    seconds = getSeconds(timeUnit)
    spinner = Spinner()
    blankLine = True if end == '\r' else False
    for left in range(seconds*spinner.tickXSec, 0, -1):
        spinnerStr = spinner.generate()
        timeLeft = str(timedelta(seconds=int(left/spinner.tickXSec)))
        print(yellow(message, f"{spinnerStr} I'll retry in {timeLeft} {spinnerStr}{' '*10}"), end=end)
        end='\r'
        spinner.nextTick()
        sleep(1/spinner.tickXSec)
    if blankLine:
        print()


def getSeconds(timeUnit: str):
    """timeUnit: 30s|8m|2h"""
    timeUnit = timeUnit.strip()
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600}
    unit = timeUnit[-1].lower()
    seconds = int(timeUnit.strip()[:-1]) * seconds_per_unit[unit]
    return seconds


def getTimeUnits(seconds: int) -> str:
    """Convert seconds to a detailed time unit string (e.g., 1h 35m 10s)."""
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    time_units = []
    if hours > 0:
        time_units.append(f"{hours}h")
    if minutes > 0:
        time_units.append(f"{minutes}m")
    if seconds > 0 or not time_units:
        time_units.append(f"{seconds}s")

    return ' '.join(time_units)


def getDatetimeNow() -> int:
    return int(datetime.now().timestamp())


def getDatetimeNowStr() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
    spinner:str = ''

    def __init__(self):
        self.spinner = self.SPINNERS[random.randint(0, len(self.SPINNERS)-1)]

    def nextTick(self):
        self.spinItem = self.spinItem + \
            1 if self.spinItem+1 < len(self.spinner) else 0

    def generate(self):
        return self.spinner[self.spinItem]*5


def createFolder(filename: str) -> Path:
    path = Path(filename)
    path.parent.mkdir(exist_ok=True, parents=True)
    return path


def listFiles(folder: Path) -> list[str]:
    return [f for f in os.listdir(folder.absolute()) if isfile(join(folder, f))]


def getSrcPath() -> str:
    return str(Path(os.getcwd()))


def isMacOS() -> bool:
    import platform
    return platform.system() == 'Darwin'

def isWindowsOS() -> bool:
    import platform
    return platform.system() == 'Windows'

def isLinuxOS() -> bool:
    import platform
    return platform.system() == 'Linux'
