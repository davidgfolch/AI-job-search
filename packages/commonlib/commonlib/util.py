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
    spinner = None

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


def getcwd() -> str:
    return os.getcwd()


def getSrcPath() -> str:
    return str(Path(os.getcwd()))


def getEnvInt(key: str, default: int = 0) -> int:
    """Get environment variable as integer"""
    try:
        value = getEnv(key)
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def getEnvFloat(key: str, default: float = 0.0) -> float:
    """Get environment variable as float"""
    try:
        value = getEnv(key)
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def formatNumber(number):
    """Format number with thousands separator"""
    if isinstance(number, (int, float)):
        return f"{number:,}"
    return str(number)


def formatBytes(bytes_value):
    """Format bytes to human readable format"""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 ** 2:
        return f"{bytes_value / 1024:.1f} KB"
    elif bytes_value < 1024 ** 3:
        return f"{bytes_value / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_value / (1024 ** 3):.1f} GB"


def formatPercentage(value):
    """Format decimal as percentage"""
    return f"{value * 100:.1f}%"


def isValidUrl(url):
    """Check if URL is valid"""
    if not url:
        return False
    return url.startswith(('http://', 'https://'))


def isValidEmail(email):
    """Check if email is valid"""
    if not email:
        return False
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def cleanText(text):
    """Clean text by removing extra whitespace"""
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text.strip())


def parseDate(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return None
    try:
        from datetime import datetime
        # Try different formats
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def formatDate(date_obj, format_str='%Y-%m-%d %H:%M:%S'):
    """Format datetime object to string"""
    if not date_obj:
        return ''
    try:
        return date_obj.strftime(format_str)
    except Exception:
        return ''


def getCurrentTimestamp():
    """Get current timestamp"""
    import time
    return time.time()


def safeInt(value, default=0):
    """Safely convert value to int"""
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def safeFloat(value, default=0.0):
    """Safely convert value to float"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safeBool(value, default=False):
    """Safely convert value to bool"""
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        return bool(value)
    except (ValueError, TypeError):
        return default
