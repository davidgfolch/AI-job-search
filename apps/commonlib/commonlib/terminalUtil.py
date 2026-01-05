import random
from datetime import timedelta
from .wake_timer import WakeableTimer
from .terminalColor import yellow
from .systemUtil import isDocker
from .dateUtil import getSeconds

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
    for left in range(seconds*spinner.tickXSec, 0, -1):
        spinnerStr = spinner.generate()
        timeLeft = str(timedelta(seconds=int(left/spinner.tickXSec)))
        print(yellow(message, f"{spinnerStr} I'll retry in {timeLeft} {spinnerStr}{' '*10}"), end=end)
        end='\r'
        spinner.nextTick()
        WakeableTimer().wait(1/spinner.tickXSec)
    if blankLine:
        print()

def consoleTimerDocker(message: str, timeUnit: str):
    """timeUnit: 30s|8m|2h"""
    seconds = getSeconds(timeUnit)
    timeLeft = str(timedelta(seconds=seconds))
    print(yellow(message, f" I'll retry in {timeLeft} "), end='', flush=True)
    for _ in range(seconds):
        print('.', end='', flush=True)
        WakeableTimer().wait(1)
    print()

def consoleTimer(message: str, timeUnit: str, end='\r'):
    if isDocker():
        consoleTimerDocker(message, timeUnit)
    else:
        _consoleTimerLocal(message, timeUnit, end)
