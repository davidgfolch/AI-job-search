HEADER = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
ORANGE = '\033[38;5;208m'
RED = '\033[91m'
MAGENTA = '\033[35m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
RESET = '\033[0m'
__RESET = RESET


def green(*text: str):
    return GREEN + ''.join(text) + __RESET


def yellow(*text: str):
    return YELLOW + ''.join(text) + __RESET


def red(*text: str):
    return RED + ''.join(text) + __RESET


def blue(*text: str):
    return BLUE + ''.join(text) + __RESET


def cyan(*text: str):
    return CYAN + ''.join(text) + __RESET


def magenta(*text: str):
    return MAGENTA + ''.join(text) + __RESET


def printHR(colorFnc=None):
    if colorFnc:
        print(colorFnc('-'*150))
    else:
        print('-'*150)
