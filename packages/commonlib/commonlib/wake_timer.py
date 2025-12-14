import ctypes
import math
import platform
import time

if platform.system() == 'Windows':
    from ctypes import wintypes
else:
    wintypes = None

# Windows API constants
CREATE_WAITABLE_TIMER_MANUAL_RESET = 0x00000001
TIMER_ALL_ACCESS = 0x1F0003
INFINITE = 0xFFFFFFFF
WAIT_OBJECT_0 = 0x00000000

class WakeableTimer:
    """
    Timer that can wake the Windows system from suspend state.
    Uses CreateWaitableTimer and SetWaitableTimer Windows APIs.
    """
    def __init__(self):
        self.os_type = platform.system()
    
    def wait(self, seconds: int):
        """
        Wait for the specified number of seconds.
        If on Windows, uses a waitable timer that can wake the system.
        On other OS, falls back to time.sleep.
        """
        # This block is used to exclude Windows-specific code from coverage on non-Windows platforms.
        # The pyproject.toml is configured to exclude lines starting with "if platform.system() == 'Windows':"
        if platform.system() == 'Windows':
            # Windows implementation
            kernel32 = ctypes.windll.kernel32
            
            # Define argtypes for robustness
            # HANDLE CreateWaitableTimerW(LPSECURITY_ATTRIBUTES lpTimerAttributes, BOOL bManualReset, LPCWSTR lpTimerName);
            kernel32.CreateWaitableTimerW.argtypes = [ctypes.c_void_p, wintypes.BOOL, ctypes.c_wchar_p]
            kernel32.CreateWaitableTimerW.restype = wintypes.HANDLE

            # BOOL SetWaitableTimer(HANDLE hTimer, const LARGE_INTEGER *lpDueTime, LONG lPeriod, PTIMERAPCROUTINE pfnCompletionRoutine, LPVOID lpArgToCompletionRoutine, BOOL fResume);
            kernel32.SetWaitableTimer.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.LARGE_INTEGER),
                wintypes.LONG,
                ctypes.c_void_p,
                ctypes.c_void_p,
                wintypes.BOOL
            ]
            kernel32.SetWaitableTimer.restype = wintypes.BOOL

            # hTimer = CreateWaitableTimer(NULL, TRUE, NULL)
            # We use manual reset (TRUE) and no name (None)
            hTimer = kernel32.CreateWaitableTimerW(None, True, None)
            if not hTimer:
                print(f"Failed to create waitable timer. Error: {ctypes.GetLastError()}")
                time.sleep(seconds)
                return
            try:
                # SetWaitableTimer expects time in 100-nanosecond intervals.
                # Negative values indicate relative time.
                # 1 second = 10,000,000 units
                duetime = -int(seconds * 10_000_000)
                large_integer = wintypes.LARGE_INTEGER(duetime)
                # fResume = True (last argument) enables waking the computer
                success = kernel32.SetWaitableTimer(
                    hTimer, 
                    ctypes.byref(large_integer), 
                    0, 
                    None, 
                    None, 
                    True
                )
                if not success:
                    print(f"Failed to set waitable timer. Error: {ctypes.GetLastError()}")
                    time.sleep(seconds)
                    return
                # Wait for the timer to signal
                result = kernel32.WaitForSingleObject(hTimer, INFINITE)
                if result != WAIT_OBJECT_0:
                    print(f"WaitForSingleObject failed with result: {result}. Error: {ctypes.GetLastError()}")
            finally:
                kernel32.CloseHandle(hTimer)
        else:
            time.sleep(seconds)
