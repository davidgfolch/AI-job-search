"""Cross-platform advisory file locking, used by `commonlib.ollama_activity`.

Split out of `ollama_activity` so the POSIX/Windows primitives can be tested on their
own: the slot logic there only needs "lock a file descriptor without blocking, or say no".
"""
import os


def try_lock(fd: int, shared: bool) -> bool:
    """Take a lock on `fd` without blocking; `False` when somebody else holds it."""
    try:
        import fcntl
    except ImportError:  # Windows hosts: exclusive locking only, still correct but stricter
        return _try_lock_windows(fd)
    flags = (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB
    try:
        fcntl.flock(fd, flags)
        return True
    except OSError:
        return False


def _try_lock_windows(fd: int) -> bool:
    try:
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        return True
    except (ImportError, OSError):
        return False


def unlock(fd: int) -> None:
    try:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)
        return
    except ImportError:
        pass
    except OSError:
        return
    try:
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    except (ImportError, OSError):
        pass
