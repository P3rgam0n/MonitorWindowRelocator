import ctypes
from ctypes import wintypes
import time

# System DPI awareness setup for Windows 10/11
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
    except Exception:
        pass

user32 = ctypes.windll.user32

# Win32 Constants
MONITOR_DEFAULTTONEAREST = 2
SW_RESTORE = 9
SW_MAXIMIZE = 3
SWP_NOZORDER = 0x0004
SWP_SHOWWINDOW = 0x0040
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
GA_ROOT = 2

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

class MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', ctypes.c_ulong),
        ('szDevice', ctypes.c_wchar * 32)
    ]

# Win32 function signatures
user32.GetDesktopWindow.restype = wintypes.HWND
user32.GetForegroundWindow.restype = wintypes.HWND
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL
user32.IsZoomed.argtypes = [wintypes.HWND]
user32.IsZoomed.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.SetWindowPos.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

def get_monitors():
    """Returns a list of all active monitors with rect, work area, device name, and primary flag."""
    monitors = []
    
    def callback(hMonitor, hdcMonitor, lprcMonitor, lParam):
        info = MONITORINFOEX()
        info.cbSize = ctypes.sizeof(MONITORINFOEX)
        if user32.GetMonitorInfoW(hMonitor, ctypes.byref(info)):
            monitors.append({
                'handle': hMonitor,
                'device': info.szDevice,
                'rect': (info.rcMonitor.left, info.rcMonitor.top, info.rcMonitor.right, info.rcMonitor.bottom),
                'work': (info.rcWork.left, info.rcWork.top, info.rcWork.right, info.rcWork.bottom),
                'work_width': info.rcWork.right - info.rcWork.left,
                'work_height': info.rcWork.bottom - info.rcWork.top,
                'primary': bool(info.dwFlags & 1)
            })
        return True

    MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(callback), 0)
    
    # Sort monitors by X position left to right
    monitors.sort(key=lambda m: m['rect'][0])
    return monitors

def get_primary_monitor(monitors):
    """Finds and returns the primary monitor dictionary from the list of monitors."""
    for m in monitors:
        if m['primary']:
            return m
    return monitors[0] if monitors else None

def get_cursor_monitor_index(monitors):
    """Returns the index and dictionary of the monitor currently containing the mouse cursor."""
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    for idx, mon in enumerate(monitors):
        l, t, r, b = mon['rect']
        if l <= pt.x < r and t <= pt.y < b:
            return idx, mon
    # Fallback to nearest/first
    return 0, monitors[0] if monitors else None

def get_desktop_windows():
    """Lists all open titled application windows across input desktop and current window station."""
    windows = []
    seen_hwnds = set()

    def inspect_hwnd(hwnd):
        if hwnd in seen_hwnds:
            return
        if not user32.IsWindowVisible(hwnd):
            return
        
        # Must be root window
        if user32.GetAncestor(hwnd, GA_ROOT) != hwnd:
            return

        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return
        
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.strip()
        
        # Ignore desktop / shell elements (English & Polish OS titles)
        ignored_titles = (
            "Program Manager",
            "Settings",
            "NVIDIA GeForce Overlay",
            "Windows Input Experience",
            "Środowisko wprowadzania danych w systemie Windows"
        )
        if not title or title in ignored_titles:
            return

        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if (ex_style & WS_EX_TOOLWINDOW) and not (ex_style & WS_EX_APPWINDOW):
            return

        rect = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return

        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w <= 20 or h <= 20:
            return

        seen_hwnds.add(hwnd)
        windows.append({
            'hwnd': hwnd,
            'title': title,
            'rect': (rect.left, rect.top, rect.right, rect.bottom),
            'width': w,
            'height': h,
            'is_minimized': bool(user32.IsIconic(hwnd)),
            'is_maximized': bool(user32.IsZoomed(hwnd))
        })

    # Strategy 1: OpenInputDesktop + EnumDesktopWindows
    try:
        desk = user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_ENUMERATE
        if desk:
            ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
            def desk_cb(h, l):
                inspect_hwnd(h)
                return 1
            user32.EnumDesktopWindows(desk, ENUMPROC(desk_cb), 0)
            user32.CloseDesktop(desk)
    except Exception:
        pass

    # Strategy 2: Standard EnumWindows fallback
    ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
    def enum_cb(h, l):
        inspect_hwnd(h)
        return 1
    user32.EnumWindows(ENUMPROC(enum_cb), 0)

    return windows

def get_active_window():
    """Gets current foreground active window info."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value.strip()

    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))

    return {
        'hwnd': hwnd,
        'title': title,
        'rect': (rect.left, rect.top, rect.right, rect.bottom),
        'width': rect.right - rect.left,
        'height': rect.bottom - rect.top,
        'is_minimized': bool(user32.IsIconic(hwnd)),
        'is_maximized': bool(user32.IsZoomed(hwnd))
    }

def move_window_to_monitor(hwnd, target_monitor, force_restore_maximize=True):
    """Moves a specified window handle (hwnd) to target_monitor dict."""
    if not hwnd or not user32.IsWindow(hwnd):
        return False

    is_min = bool(user32.IsIconic(hwnd))
    is_max = bool(user32.IsZoomed(hwnd))

    if is_min:
        user32.ShowWindow(hwnd, SW_RESTORE)

    if is_max and force_restore_maximize:
        user32.ShowWindow(hwnd, SW_RESTORE)

    # Current window dimensions
    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    win_w = rect.right - rect.left
    win_h = rect.bottom - rect.top

    wl, wt, wr, wb = target_monitor['work']
    target_w = target_monitor['work_width']
    target_h = target_monitor['work_height']

    # Scale down if larger than target monitor work area
    new_w = min(win_w, int(target_w * 0.95))
    new_h = min(win_h, int(target_h * 0.95))
    if new_w < 400:
        new_w = min(800, target_w)
    if new_h < 300:
        new_h = min(600, target_h)

    # Center window inside target work area
    new_x = wl + max(0, (target_w - new_w) // 2)
    new_y = wt + max(0, (target_h - new_h) // 2)

    # Move window
    res = user32.SetWindowPos(hwnd, 0, new_x, new_y, new_w, new_h, SWP_NOZORDER | SWP_SHOWWINDOW)

    if is_max and force_restore_maximize:
        time.sleep(0.05)
        user32.ShowWindow(hwnd, SW_MAXIMIZE)

    user32.SetForegroundWindow(hwnd)
    return bool(res)

def is_rect_on_any_monitor(rect, monitors):
    """Checks if a window rect is visible on at least one currently active monitor."""
    l, t, r, b = rect
    win_cx = (l + r) // 2
    win_cy = (t + b) // 2

    for m in monitors:
        ml, mt, mr, mb = m['rect']
        if ml <= win_cx < mr and mt <= win_cy < mb:
            return True
    return False

def move_active_to_cursor():
    """Moves currently focused window to monitor under mouse cursor."""
    monitors = get_monitors()
    if not monitors:
        return False
    
    idx, cur_mon = get_cursor_monitor_index(monitors)
    fg = get_active_window()
    if not fg or not fg['hwnd']:
        return False

    return move_window_to_monitor(fg['hwnd'], cur_mon)

def move_active_to_monitor_index(monitor_index_1based):
    """Moves active window to Monitor 1, 2, or 3."""
    monitors = get_monitors()
    if not monitors:
        return False
    
    target_idx = max(0, min(monitor_index_1based - 1, len(monitors) - 1))
    target_mon = monitors[target_idx]
    
    fg = get_active_window()
    if not fg or not fg['hwnd']:
        return False

    return move_window_to_monitor(fg['hwnd'], target_mon)

def gather_offscreen_windows():
    """Scans all windows and moves off-screen or secondary display windows to Primary Monitor."""
    monitors = get_monitors()
    if not monitors:
        return 0

    primary_mon = get_primary_monitor(monitors)
    windows = get_desktop_windows()

    moved_count = 0
    for w in windows:
        # Check if center of window is off-screen (outside all active monitors)
        if not is_rect_on_any_monitor(w['rect'], monitors):
            if move_window_to_monitor(w['hwnd'], primary_mon):
                moved_count += 1

    return moved_count
