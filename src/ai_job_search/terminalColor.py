HEADER = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
__RESET = '\033[0m'


def green(text: str):
    return GREEN + ''.join(text) + __RESET


def yellow(*text: str):
    return YELLOW + ''.join(text) + __RESET


def red(*text: str):
    return RED + ''.join(text) + __RESET
