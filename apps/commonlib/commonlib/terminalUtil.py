import random
import re
from datetime import timedelta
from .wake_timer import WakeableTimer
from .terminalColor import yellow, cyan
from .systemUtil import isDocker
from .dateUtil import getSeconds
from .observability import get_logger

logger = get_logger("commonlib.terminalUtil")

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)

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

def _consoleTimerLocal(message: str, timeUnit: str, end='\r'):
    """timeUnit: 30s|8m|2h"""
    seconds = getSeconds(timeUnit)
    spinner = Spinner()
    blankLine = True if end == '\r' else False
    timeLeft = str(timedelta(seconds=seconds))
    logger.info("timer.started", message=_strip_ansi(message), time_unit=timeUnit, seconds=seconds, in_place=blankLine)
    print(cyan(f"{message} {timeLeft}"))
    for left in range(seconds*spinner.tickXSec, 0, -1):
        spinnerStr = spinner.generate()
        timeLeft = str(timedelta(seconds=int(left/spinner.tickXSec)))
        print(yellow(message, f" {spinnerStr} I'll retry in {timeLeft} {spinnerStr}{' '*10}"), end=end)
        end='\r'
        spinner.nextTick()
        WakeableTimer().wait(1/spinner.tickXSec)
    if blankLine:
        print()
    logger.info("timer.completed", message=_strip_ansi(message), time_unit=timeUnit, seconds=seconds)

def consoleTimerDocker(message: str, timeUnit: str):
    """timeUnit: 30s|8m|2h"""
    seconds = getSeconds(timeUnit)
    logger.info("timer.started", message=_strip_ansi(message), time_unit=timeUnit, seconds=seconds)
    WakeableTimer().wait(seconds)

def consoleTimer(message: str, timeUnit: str, end='\r'):
    logger.debug("timer.requested", message=_strip_ansi(message), time_unit=timeUnit)
    if isDocker():
        consoleTimerDocker(message, timeUnit)
    else:
        _consoleTimerLocal(message, timeUnit, end)
