import ctypes
import platform
import sys
from contextlib import AbstractContextManager

if platform.system() == 'Windows':
    from ctypes import wintypes

    # Windows API Constants and Structures
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

    POWER_REQUEST_CONTEXT_VERSION = 0
    POWER_REQUEST_CONTEXT_SIMPLE_STRING = 0x1

    PowerRequestSystemRequired = 0
    PowerRequestDisplayRequired = 1

    class DetailedStructure(ctypes.Structure):
        _fields_ = [
            ("LocalizedStringModule", wintypes.HMODULE),
            ("LocalizedStringId", wintypes.ULONG),
            ("ReasonStringCount", wintypes.ULONG),
            ("ReasonStrings", ctypes.POINTER(wintypes.LPWSTR)),
        ]

    class ReasonUnion(ctypes.Union):
        _fields_ = [
            ("Detailed", DetailedStructure),
            ("SimpleReasonString", wintypes.LPWSTR),
        ]

    class REASON_CONTEXT(ctypes.Structure):
        _fields_ = [
            ("Version", wintypes.ULONG),
            ("Flags", wintypes.DWORD),
            ("Reason", ReasonUnion),
        ]
else:
    # Define constants/placeholders for non-Windows systems to avoid name errors in IDEs or if accessed
    wintypes = None 
    ES_CONTINUOUS = 0
    ES_SYSTEM_REQUIRED = 0
    ES_DISPLAY_REQUIRED = 0

class KeepSystemAwake(AbstractContextManager):
    """
    Context manager to prevent the system from going to sleep or turning off the display
    while code is executing. Supports Windows via PowerCreateRequest (Modern) 
    and SetThreadExecutionState (Legacy).
    """
    def __init__(self, reason="AI Job Search Task Running"):
        self.reason = reason
        self.power_request_handle = None

    def __enter__(self):
        if platform.system() == 'Windows':
            print("Preventing Windows system sleep...")
            if not self._try_power_request():
                self._use_legacy_api(enable=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if platform.system() == 'Windows':
            print("Allowing Windows system sleep...")
            if self.power_request_handle:
                self._clear_power_request()
            else:
                self._use_legacy_api(enable=False)

    # This block is used to exclude Windows-specific code from coverage on non-Windows platforms.
    # The pyproject.toml is configured to exclude lines starting with "if platform.system() == 'Windows':"
    if platform.system() == 'Windows':
        def _try_power_request(self):
            try:
                kernel32 = ctypes.windll.kernel32
                
                # Setup the reason structure
                reason_context = REASON_CONTEXT()
                reason_context.Version = POWER_REQUEST_CONTEXT_VERSION
                reason_context.Flags = POWER_REQUEST_CONTEXT_SIMPLE_STRING
                reason_context.Reason.SimpleReasonString = ctypes.c_wchar_p(self.reason)

                # Create the request
                # PowerCreateRequest = kernel32.PowerCreateRequest
                # Define argtypes to be safe
                kernel32.PowerCreateRequest.argtypes = [ctypes.POINTER(REASON_CONTEXT)]
                kernel32.PowerCreateRequest.restype = wintypes.HANDLE

                self.power_request_handle = kernel32.PowerCreateRequest(ctypes.byref(reason_context))
                
                if not self.power_request_handle or self.power_request_handle == -1:
                    print(f"PowerCreateRequest failed. Error: {ctypes.GetLastError()}")
                    self.power_request_handle = None
                    return False

                # Set the request types
                # PowerSetRequest(Handle, RequestType)
                kernel32.PowerSetRequest.argtypes = [wintypes.HANDLE, ctypes.c_int]
                kernel32.PowerSetRequest.restype = wintypes.BOOL

                success_sys = kernel32.PowerSetRequest(self.power_request_handle, PowerRequestSystemRequired)
                success_disp = kernel32.PowerSetRequest(self.power_request_handle, PowerRequestDisplayRequired)
                
                if not success_sys and not success_disp:
                     print(f"PowerSetRequest failed. Error: {ctypes.GetLastError()}")
                     self._close_handle()
                     return False
                
                return True

            except Exception as e:
                print(f"Error using Power Request API: {e}")
                self._close_handle()
                return False

        def _clear_power_request(self):
            if not self.power_request_handle:
                return
            
            try:
                kernel32 = ctypes.windll.kernel32
                kernel32.PowerClearRequest.argtypes = [wintypes.HANDLE, ctypes.c_int]
                kernel32.PowerClearRequest.restype = wintypes.BOOL

                kernel32.PowerClearRequest(self.power_request_handle, PowerRequestSystemRequired)
                kernel32.PowerClearRequest(self.power_request_handle, PowerRequestDisplayRequired)
            finally:
                self._close_handle()

        def _close_handle(self):
            if self.power_request_handle:
                ctypes.windll.kernel32.CloseHandle(self.power_request_handle)
                self.power_request_handle = None

        def _use_legacy_api(self, enable: bool):
            if enable:
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                )
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
