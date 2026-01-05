import os
import platform

def isDocker() -> bool:
    if os.path.exists('/.dockerenv'): return True
    try:
        with open('/proc/1/cgroup', 'rt') as f: return 'docker' in f.read()
    except Exception: return False

def isMacOS() -> bool:
    return platform.system() == 'Darwin'

def isWindowsOS() -> bool:
    return platform.system() == 'Windows'

def isLinuxOS() -> bool:
    return platform.system() == 'Linux'
