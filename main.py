"""
Monitor Window Relocator
========================
A lightweight, zero-dependency Windows utility that relocates windows from
disconnected, powered-off, or sleeping monitors back onto your active display.

Zero external dependencies: built strictly on the Python Standard Library (ctypes, tkinter).
"""

import argparse
import ctypes
from ctypes import wintypes
import json
import locale
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

# Configure UTF-8 encoding for console stdout/stderr on Windows
if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr is not None and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ============================================================================
# Section 1: Win32 API & System Initialization
# ============================================================================

# Enable Per-Monitor High-DPI Awareness on Windows 10/11
try:
    # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4 (Win 10 1703+)
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2 (Win 8.1+)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

try:
    dwmapi = ctypes.windll.dwmapi
except Exception:
    dwmapi = None

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
DESKTOP_ENUMERATE = 0x0100
DESKTOP_SWITCHDESKTOP = 0x0040
DWMWA_CLOAKED = 14

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

VK_M = 0x4D
VK_G = 0x47
VK_1 = 0x31
VK_2 = 0x32
VK_3 = 0x33

class POINT(ctypes.Structure):
    """Win32 POINT structure."""
    _fields_ = [
        ('x', ctypes.c_long),
        ('y', ctypes.c_long)
    ]

class RECT(ctypes.Structure):
    """Win32 RECT structure with width and height helper properties."""
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

class WINDOWPLACEMENT(ctypes.Structure):
    """Win32 WINDOWPLACEMENT structure for retrieving normal (restored) window geometry."""
    _fields_ = [
        ('length', ctypes.c_uint),
        ('flags', ctypes.c_uint),
        ('showCmd', ctypes.c_uint),
        ('ptMinPosition', POINT),
        ('ptMaxPosition', POINT),
        ('rcNormalPosition', RECT)
    ]

class MONITORINFOEX(ctypes.Structure):
    """Win32 MONITORINFOEXW structure."""
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', ctypes.c_ulong),
        ('szDevice', ctypes.c_wchar * 32)
    ]

# Explicit 64-bit and 32-bit Win32 function signatures
user32.GetDesktopWindow.restype = wintypes.HWND
user32.GetForegroundWindow.restype = wintypes.HWND
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
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
user32.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWPLACEMENT)]
user32.GetWindowPlacement.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.SetWindowPos.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
user32.GetAncestor.restype = wintypes.HWND
user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFOEX)]
user32.GetMonitorInfoW.restype = wintypes.BOOL
user32.MonitorFromPoint.argtypes = [wintypes.POINT, ctypes.c_uint]
user32.MonitorFromPoint.restype = wintypes.HMONITOR
user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.c_void_p, ctypes.c_void_p, wintypes.LPARAM]
user32.EnumDisplayMonitors.restype = wintypes.BOOL
user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL

user32.OpenInputDesktop.argtypes = [ctypes.c_uint, wintypes.BOOL, ctypes.c_uint]
user32.OpenInputDesktop.restype = wintypes.HANDLE
user32.CloseDesktop.argtypes = [wintypes.HANDLE]
user32.CloseDesktop.restype = wintypes.BOOL
user32.SetThreadDesktop.argtypes = [wintypes.HANDLE]
user32.SetThreadDesktop.restype = wintypes.BOOL
user32.EnumDesktopWindows.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.LPARAM]
user32.EnumDesktopWindows.restype = wintypes.BOOL

user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
user32.PeekMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = ctypes.c_ssize_t
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int

kernel32.GetUserDefaultUILanguage.argtypes = []
kernel32.GetUserDefaultUILanguage.restype = wintypes.USHORT

if dwmapi:
    try:
        dwmapi.DwmGetWindowAttribute.argtypes = [wintypes.HWND, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong]
        dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long
    except Exception:
        pass

if hasattr(user32, 'GetWindowLongPtrW'):
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    _get_window_long = user32.GetWindowLongPtrW
else:
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long
    _get_window_long = user32.GetWindowLongW


def ensure_input_desktop():
    """Attaches the calling thread to the interactive input desktop if accessible."""
    try:
        # 0x01FF = DESKTOP_ALL_PERMISSIONS
        desk = user32.OpenInputDesktop(0, False, 0x01FF)
        if desk:
            user32.SetThreadDesktop(desk)
            user32.CloseDesktop(desk)
    except Exception:
        pass


# ============================================================================
# Section 2: Internationalization (i18n) & Configuration
# ============================================================================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

LANGUAGES = {
    "en": "English",
    "pl": "Polski"
}

TRANSLATIONS = {
    "en": {
        # App Info
        "app_title": "🖥️ Monitor Window Relocator",
        "app_window_title": "Monitor Window Relocator v1.1",
        "app_subtitle": "Quickly move windows from turned-off or sleeping monitors to your active screen.",

        # Status Frame
        "status_frame_title": " Monitor & System Status ",
        "lbl_monitors_loading": "Detected monitors: loading...",
        "lbl_monitors_format": "Detected monitors ({count}): {monitors}",
        "lbl_mon_primary": " (Primary)",
        "lbl_cursor_loading": "Mouse cursor: loading...",
        "lbl_cursor_format": "Mouse cursor is on: Monitor {index} ({device})",
        "lbl_active_none": "Active window: Monitor Window Relocator (or none)",
        "lbl_active_format": "Active window: '{title}'",

        # Actions Frame
        "actions_frame_title": " Quick Actions & Global Hotkeys ",
        "btn_move_to_cursor": "🎯 Move Active Window to Mouse (Ctrl+Alt+M)",
        "btn_gather_offscreen": "🧹 Gather Hidden Windows to Primary Screen (Ctrl+Alt+G)",
        "lbl_move_active_to": "Move active window to:",
        "btn_mon_1": "Monitor 1 (Ctrl+Alt+1)",
        "btn_mon_2": "Monitor 2 (Ctrl+Alt+2)",
        "btn_mon_3": "Monitor 3 (Ctrl+Alt+3)",

        # Windows List Frame
        "windows_frame_title": " Open Applications & Windows ",
        "col_title": "Window Title",
        "col_pos": "Coordinates (X, Y)",
        "col_size": "Size (W x H)",
        "col_hwnd": "HWND",

        # Bottom Controls & Status
        "btn_refresh": "🔄 Refresh Window List",
        "btn_move_selected": "🎯 Move Selected Window to Mouse",
        "status_ready": "Ready",
        "status_moved_to_cursor": "Moved active window to screen under mouse cursor.",
        "status_no_active_window": "No active window to move.",
        "status_gathered": "Gathered {count} hidden window(s) to primary screen.",
        "status_moved_to_mon": "Moved active window to Monitor {index}.",
        "status_move_failed": "Failed to move window.",
        "status_moved_selected": "Moved '{title}' to Monitor {index}.",
        "status_hotkey_triggered": "Hotkey triggered: {name}",

        # Dialogs & Menus
        "dialog_info_title": "Information",
        "dialog_select_window_first": "Please select a window from the list first.",
        "menu_settings": "Settings",
        "menu_language": "Language",
        "lbl_language": "Language:",
        "tag_minimized": " (Minimized)",
        "tag_maximized": " (Maximized)",
        "btn_mon_n": "Monitor {index}",

        # CLI Output
        "cli_gathered": "Gathered {count} hidden window(s) to primary screen.",
        "cli_moved_to_cursor": "Moved active window to monitor under mouse cursor.",
        "cli_no_active_window": "No active window found.",
        "cli_moved_to_mon": "Moved active window to Monitor {index}.",
        "cli_invalid_mon": "Invalid monitor index: {index}",

        # Logs
        "log_reg_failed": "[HotkeyManager] Failed to register hotkey: {name}",
        "log_action_error": "[HotkeyManager] Error executing action {name}: {error}",
        "log_unregistered": "[HotkeyManager] Successfully unregistered hotkeys."
    },
    "pl": {
        # App Info
        "app_title": "🖥️ Monitor Window Relocator",
        "app_window_title": "Monitor Window Relocator v1.1",
        "app_subtitle": "Szybkie przenoszenie okien z wyłączonych lub uśpionych monitorów na aktywny ekran.",

        # Status Frame
        "status_frame_title": " Stan Monitorów i Systemu ",
        "lbl_monitors_loading": "Wykryte monitory: wczytywanie...",
        "lbl_monitors_format": "Wykryte monitory ({count}): {monitors}",
        "lbl_mon_primary": " (Główny)",
        "lbl_cursor_loading": "Kursor myszy: wczytywanie...",
        "lbl_cursor_format": "Kursor myszy znajduje się na: Monitor {index} ({device})",
        "lbl_active_none": "Aktywne okno: Monitor Window Relocator (lub brak)",
        "lbl_active_format": "Aktywne okno: '{title}'",

        # Actions Frame
        "actions_frame_title": " Szybkie Akcje i Skróty Klawiszowe ",
        "btn_move_to_cursor": "🎯 Przenieś aktywne okno do myszy (Ctrl+Alt+M)",
        "btn_gather_offscreen": "🧹 Ściągnij ukryte okna na Ekran Główny (Ctrl+Alt+G)",
        "lbl_move_active_to": "Przenieś aktywne okno na:",
        "btn_mon_1": "Monitor 1 (Ctrl+Alt+1)",
        "btn_mon_2": "Monitor 2 (Ctrl+Alt+2)",
        "btn_mon_3": "Monitor 3 (Ctrl+Alt+3)",

        # Windows List Frame
        "windows_frame_title": " Otwarte Aplikacje i Okna ",
        "col_title": "Tytuł Okna",
        "col_pos": "Współrzędne (X, Y)",
        "col_size": "Rozmiar (W x H)",
        "col_hwnd": "HWND",

        # Bottom Controls & Status
        "btn_refresh": "🔄 Odśwież listę okien",
        "btn_move_selected": "🎯 Przenieś zaznaczone okno do myszy",
        "status_ready": "Gotowy",
        "status_moved_to_cursor": "Przeniesiono aktywne okno na ekran z kursorem myszy.",
        "status_no_active_window": "Brak aktywnego okna do przeniesienia.",
        "status_gathered": "Ściągnięto {count} niewidocznych okien na ekran główny.",
        "status_moved_to_mon": "Przeniesiono aktywne okno na Monitor {index}.",
        "status_move_failed": "Nie udało się przenieść okna.",
        "status_moved_selected": "Przeniesiono '{title}' na Monitor {index}.",
        "status_hotkey_triggered": "Uruchomiono skrót: {name}",

        # Dialogs & Menus
        "dialog_info_title": "Informacja",
        "dialog_select_window_first": "Zaznacz najpierw okno z listy otwartych aplikacji.",
        "menu_settings": "Ustawienia",
        "menu_language": "Język",
        "lbl_language": "Język:",
        "tag_minimized": " (Zminimalizowane)",
        "tag_maximized": " (Zmaksymalizowane)",
        "btn_mon_n": "Monitor {index}",

        # CLI Output
        "cli_gathered": "Ściągnięto {count} niewidocznych okien na ekran główny.",
        "cli_moved_to_cursor": "Przeniesiono aktywne okno na monitor pod kursorem.",
        "cli_no_active_window": "Nie znaleziono aktywnego okna.",
        "cli_moved_to_mon": "Przeniesiono aktywne okno na Monitor {index}.",
        "cli_invalid_mon": "Niepoprawny numer monitora: {index}",

        # Logs
        "log_reg_failed": "[HotkeyManager] Nie udało się zarejestrować skrótu: {name}",
        "log_action_error": "[HotkeyManager] Błąd podczas wykonywania akcji {name}: {error}",
        "log_unregistered": "[HotkeyManager] Pomyślnie wyrejestrowano skróty klawiszowe."
    }
}

_current_lang = "en"


def detect_system_language():
    """Detects whether Windows UI language or user locale is Polish; defaults to English."""
    try:
        ui_lang = kernel32.GetUserDefaultUILanguage()
        if ui_lang == 0x0415:  # Polish (pl-PL)
            return "pl"
    except Exception:
        pass

    try:
        loc = locale.getlocale()[0]
        if loc and "polish" in loc.lower():
            return "pl"
    except Exception:
        pass

    return "en"


def load_config():
    """Loads configuration including language preference, or auto-detects system language."""
    global _current_lang
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language")
                if lang in LANGUAGES:
                    _current_lang = lang
                    return
        except Exception:
            pass
    _current_lang = detect_system_language()


def save_config():
    """Saves language preference to config.json."""
    try:
        data = {"language": _current_lang}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def set_language(lang_code):
    """Sets active language code ('en' or 'pl') and saves preference."""
    global _current_lang
    if lang_code in LANGUAGES:
        _current_lang = lang_code
        save_config()


def get_language():
    """Returns currently active language code."""
    return _current_lang


def t(key, **kwargs):
    """Retrieves localized string for key in current language with optional formatting."""
    lang_dict = TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


# Initialize config & language
load_config()


# ============================================================================
# Section 3: Monitor & Window Relocation Core
# ============================================================================

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
        return 1

    MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(callback), 0)

    # Fallback to primary screen metrics if EnumDisplayMonitors returns empty
    if not monitors:
        cx = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        cy = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        if cx > 0 and cy > 0:
            monitors.append({
                'handle': None,
                'device': '\\\\.\\DISPLAY1',
                'rect': (0, 0, cx, cy),
                'work': (0, 0, cx, cy),
                'work_width': cx,
                'work_height': cy,
                'primary': True
            })

    # Sort monitors spatially: left-to-right, then top-to-bottom
    monitors.sort(key=lambda m: (m['rect'][0], m['rect'][1]))
    return monitors


def get_primary_monitor(monitors):
    """Finds and returns primary monitor dictionary from list of monitors."""
    for m in monitors:
        if m.get('primary'):
            return m
    return monitors[0] if monitors else None


def get_cursor_monitor_index(monitors):
    """Returns the index and dictionary of the monitor currently containing (or closest to) the mouse cursor."""
    if not monitors:
        return 0, None

    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))

    # Fast path: use Win32 MonitorFromPoint handle matching
    try:
        h_mon = user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)
        if h_mon:
            for idx, mon in enumerate(monitors):
                if mon.get('handle') == h_mon:
                    return idx, mon
    except Exception:
        pass

    # Bounding rect check
    for idx, mon in enumerate(monitors):
        l, t_pos, r, b = mon['rect']
        if l <= pt.x < r and t_pos <= pt.y < b:
            return idx, mon

    # Fallback: find nearest monitor to cursor
    closest_idx = 0
    min_dist_sq = float('inf')
    for idx, mon in enumerate(monitors):
        l, t_pos, r, b = mon['rect']
        cx = (l + r) / 2
        cy = (t_pos + b) / 2
        dist_sq = (pt.x - cx) ** 2 + (pt.y - cy) ** 2
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            closest_idx = idx

    return closest_idx, monitors[closest_idx]


def is_rect_on_any_monitor(rect, monitors):
    """Checks if a window rect is visibly placed on at least one currently active monitor."""
    if not monitors or not rect:
        return False

    l, t_pos, r, b = rect
    win_w = r - l
    win_h = b - t_pos
    if win_w <= 0 or win_h <= 0:
        return False

    win_cx = (l + r) // 2
    win_cy = (t_pos + b) // 2

    # Check 1: Window center point is on an active monitor
    for m in monitors:
        ml, mt, mr, mb = m['rect']
        if ml <= win_cx < mr and mt <= win_cy < mb:
            return True

    # Check 2: At least 20% of window surface area overlaps an active monitor
    win_area = win_w * win_h
    for m in monitors:
        ml, mt, mr, mb = m['rect']
        ix1 = max(l, ml)
        iy1 = max(t_pos, mt)
        ix2 = min(r, mr)
        iy2 = min(b, mb)
        if ix2 > ix1 and iy2 > iy1:
            overlap = (ix2 - ix1) * (iy2 - iy1)
            if (overlap / win_area) >= 0.20:
                return True

    return False


def get_desktop_windows():
    """Lists all open titled application windows across desktop window stations."""
    ensure_input_desktop()
    windows = []
    seen_hwnds = set()

    def inspect_hwnd(hwnd):
        if not hwnd or hwnd in seen_hwnds:
            return
        seen_hwnds.add(hwnd)

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

        ignored_titles = (
            "Program Manager",
            "Settings",
            "Ustawienia",
            "NVIDIA GeForce Overlay",
            "Windows Input Experience",
            "Środowisko wprowadzania danych w systemie Windows",
            "Host środowiska powłoki systemu Windows",
            "Windows Shell Experience Host",
            "Microsoft Text Input Application"
        )
        if not title or title in ignored_titles:
            return

        # Filter out cloaked windows (suspended background UWP / shell apps)
        if dwmapi:
            try:
                cloaked = ctypes.c_int(0)
                if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0:
                    if cloaked.value != 0:
                        return
            except Exception:
                pass

        ex_style = _get_window_long(hwnd, GWL_EXSTYLE)
        if (ex_style & WS_EX_TOOLWINDOW) and not (ex_style & WS_EX_APPWINDOW):
            return

        is_min = bool(user32.IsIconic(hwnd))
        is_max = bool(user32.IsZoomed(hwnd))

        rect = RECT()
        if is_min:
            # Minimized windows report (-32000, -32000) via GetWindowRect.
            # Use GetWindowPlacement to retrieve true restored coordinates.
            wp = WINDOWPLACEMENT()
            wp.length = ctypes.sizeof(WINDOWPLACEMENT)
            if user32.GetWindowPlacement(hwnd, ctypes.byref(wp)):
                rect = wp.rcNormalPosition
            else:
                if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    return
        else:
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return

        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w <= 20 or h <= 20:
            return

        windows.append({
            'hwnd': hwnd,
            'title': title,
            'rect': (rect.left, rect.top, rect.right, rect.bottom),
            'width': w,
            'height': h,
            'is_minimized': is_min,
            'is_maximized': is_max
        })

    # Strategy 1: OpenInputDesktop + EnumDesktopWindows
    try:
        desk = user32.OpenInputDesktop(0, False, DESKTOP_ENUMERATE | DESKTOP_SWITCHDESKTOP)
        if desk:
            DESKENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            def desk_cb(h, l):
                inspect_hwnd(h)
                return 1
            user32.EnumDesktopWindows(desk, DESKENUMPROC(desk_cb), 0)
            user32.CloseDesktop(desk)
    except Exception:
        pass

    # Strategy 2: Standard EnumWindows
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_cb(h, l):
        inspect_hwnd(h)
        return 1
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    return windows


def get_active_window():
    """Gets current foreground active window info."""
    ensure_input_desktop()
    hwnd = user32.GetForegroundWindow()
    if not hwnd or not user32.IsWindow(hwnd):
        return None

    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return None

    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value.strip()
    if not title or title == "Program Manager":
        return None

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
    """Moves a specified window handle (hwnd) to the target_monitor work area."""
    ensure_input_desktop()
    if not hwnd or not user32.IsWindow(hwnd) or not target_monitor:
        return False

    is_min = bool(user32.IsIconic(hwnd))
    is_max = bool(user32.IsZoomed(hwnd))

    if is_min or (is_max and force_restore_maximize):
        user32.ShowWindow(hwnd, SW_RESTORE)

    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return False

    win_w = rect.right - rect.left
    win_h = rect.bottom - rect.top

    wl, wt, wr, wb = target_monitor['work']
    target_w = max(100, target_monitor['work_width'])
    target_h = max(100, target_monitor['work_height'])

    # Sizing: preserve natural window size, clamp only if exceeding target monitor
    if win_w <= 50 or win_h <= 50:
        new_w = min(800, target_w)
        new_h = min(600, target_h)
    else:
        new_w = min(win_w, int(target_w * 0.95))
        new_h = min(win_h, int(target_h * 0.95))

    # Center window inside target work area
    new_x = wl + max(0, (target_w - new_w) // 2)
    new_y = wt + max(0, (target_h - new_h) // 2)

    # Relocate window
    res = user32.SetWindowPos(hwnd, 0, new_x, new_y, new_w, new_h, SWP_NOZORDER | SWP_SHOWWINDOW)

    if is_max and force_restore_maximize:
        time.sleep(0.05)
        user32.ShowWindow(hwnd, SW_MAXIMIZE)

    user32.SetForegroundWindow(hwnd)
    return bool(res)


def move_active_to_cursor():
    """Moves currently focused window to the monitor under the mouse cursor."""
    monitors = get_monitors()
    if not monitors:
        return False

    idx, cur_mon = get_cursor_monitor_index(monitors)
    if not cur_mon:
        return False

    fg = get_active_window()
    if not fg or not fg['hwnd']:
        return False

    return move_window_to_monitor(fg['hwnd'], cur_mon)


def move_active_to_monitor_index(monitor_index_1based):
    """Moves active window to Monitor by 1-based index."""
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
    """Scans all windows and moves off-screen or stranded windows to the Primary Monitor."""
    ensure_input_desktop()
    monitors = get_monitors()
    if not monitors:
        return 0

    primary_mon = get_primary_monitor(monitors)
    if not primary_mon:
        return 0

    windows = get_desktop_windows()
    moved_count = 0
    for w in windows:
        if not is_rect_on_any_monitor(w['rect'], monitors):
            if move_window_to_monitor(w['hwnd'], primary_mon):
                moved_count += 1

    return moved_count


# ============================================================================
# Section 4: Global Hotkey Manager
# ============================================================================

class HotkeyManager:
    """Manages system-wide global hotkeys using Win32 RegisterHotKey."""

    def __init__(self, on_hotkey_triggered_callback=None):
        self.running = False
        self.thread = None
        self.callback = on_hotkey_triggered_callback
        self.hotkeys = [
            (1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_M, "Ctrl+Alt+M", self._action_move_cursor),
            (2, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_G, "Ctrl+Alt+G", self._action_gather),
            (3, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_1, "Ctrl+Alt+1", lambda: self._action_move_mon(1)),
            (4, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_2, "Ctrl+Alt+2", lambda: self._action_move_mon(2)),
            (5, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_3, "Ctrl+Alt+3", lambda: self._action_move_mon(3)),
        ]

    def _action_move_cursor(self):
        move_active_to_cursor()

    def _action_gather(self):
        gather_offscreen_windows()

    def _action_move_mon(self, idx):
        move_active_to_monitor_index(idx)

    def start(self):
        """Starts hotkey listener background thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops hotkey listener thread and cleanly unregisters hotkeys."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.6)

    def _run_loop(self):
        ensure_input_desktop()
        registered = []
        self.failed_hotkeys = []
        for hk_id, mods, vk, name, action in self.hotkeys:
            if user32.RegisterHotKey(None, hk_id, mods, vk):
                registered.append(hk_id)
            else:
                self.failed_hotkeys.append(name)
                if sys.stdout is not None:
                    try:
                        print(t("log_reg_failed", name=name))
                    except Exception:
                        pass

        msg = wintypes.MSG()
        try:
            while self.running:
                # PeekMessage PM_REMOVE = 1 allows non-blocking loop exit
                if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    if msg.message == WM_HOTKEY:
                        hk_id = msg.wParam
                        for id_val, mods, vk, name, action in self.hotkeys:
                            if id_val == hk_id:
                                try:
                                    action()
                                    if self.callback:
                                        self.callback(name)
                                except Exception as e:
                                    if sys.stdout is not None:
                                        try:
                                            print(t("log_action_error", name=name, error=e))
                                        except Exception:
                                            pass
                                break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    time.sleep(0.05)
        finally:
            for hk_id in registered:
                user32.UnregisterHotKey(None, hk_id)
            if sys.stdout is not None:
                try:
                    print(t("log_unregistered"))
                except Exception:
                    pass


# ============================================================================
# Section 5: Tkinter Graphical User Interface (GUI)
# ============================================================================

class WindowRelocatorApp:
    """Modern Tkinter GUI Application for Monitor Window Relocator."""

    def __init__(self, root):
        self.root = root
        self.root.geometry("820x600")
        self.root.minsize(680, 500)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.root.configure(bg="#f4f6f9")

        # Initialize hotkey manager
        self.hotkey_mgr = HotkeyManager(on_hotkey_triggered_callback=self._on_hotkey_triggered)
        self.hotkey_mgr.start()

        self._create_menu()
        self._create_widgets()
        self.retranslate_ui()
        self.refresh_all()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_menu(self):
        """Creates top menu bar with language settings."""
        self.menu_bar = tk.Menu(self.root)

        self.lang_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.lang_var = tk.StringVar(value=get_language())

        for lang_code, lang_name in LANGUAGES.items():
            self.lang_menu.add_radiobutton(
                label=lang_name,
                value=lang_code,
                variable=self.lang_var,
                command=lambda code=lang_code: self.on_language_change(code)
            )

        self.menu_bar.add_cascade(menu=self.lang_menu)
        self.root.config(menu=self.menu_bar)

    def _create_widgets(self):
        """Builds all GUI components."""
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Frame (Title + Subtitle + Language Selector)
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_sub_frame = ttk.Frame(header_frame)
        title_sub_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.title_label = ttk.Label(title_sub_frame, font=("Segoe UI", 16, "bold"))
        self.title_label.pack(anchor="w", pady=(0, 2))

        self.subtitle_label = ttk.Label(title_sub_frame, font=("Segoe UI", 9, "italic"))
        self.subtitle_label.pack(anchor="w")

        # Top-right Language Selector Combobox
        lang_selector_frame = ttk.Frame(header_frame)
        lang_selector_frame.pack(side=tk.RIGHT, anchor="ne")

        self.lbl_lang_select = ttk.Label(lang_selector_frame, font=("Segoe UI", 9))
        self.lbl_lang_select.pack(side=tk.LEFT, padx=(0, 5))

        self.combo_lang = ttk.Combobox(
            lang_selector_frame,
            values=list(LANGUAGES.values()),
            state="readonly",
            width=10
        )
        current_name = LANGUAGES.get(get_language(), "English")
        self.combo_lang.set(current_name)
        self.combo_lang.bind("<<ComboboxSelected>>", self._on_combobox_language_change)
        self.combo_lang.pack(side=tk.LEFT)

        # Status Frame
        self.status_lf = ttk.LabelFrame(main_frame, padding=10)
        self.status_lf.pack(fill=tk.X, pady=(0, 10))

        self.lbl_monitors = ttk.Label(self.status_lf, font=("Segoe UI", 9))
        self.lbl_monitors.pack(anchor="w", pady=2)

        self.lbl_cursor = ttk.Label(self.status_lf, font=("Segoe UI", 9))
        self.lbl_cursor.pack(anchor="w", pady=2)

        self.lbl_active = ttk.Label(self.status_lf, font=("Segoe UI", 9, "bold"))
        self.lbl_active.pack(anchor="w", pady=2)

        # Quick Actions Frame
        self.actions_lf = ttk.LabelFrame(main_frame, padding=10)
        self.actions_lf.pack(fill=tk.X, pady=(0, 10))

        btn_box1 = ttk.Frame(self.actions_lf)
        btn_box1.pack(fill=tk.X, pady=2)

        self.btn_cursor = ttk.Button(btn_box1, command=self.cmd_move_to_cursor)
        self.btn_cursor.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        self.btn_gather = ttk.Button(btn_box1, command=self.cmd_gather)
        self.btn_gather.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_box2 = ttk.Frame(self.actions_lf)
        btn_box2.pack(fill=tk.X, pady=(6, 0))

        self.lbl_mon_sel = ttk.Label(btn_box2, font=("Segoe UI", 9, "bold"))
        self.lbl_mon_sel.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_mon1 = ttk.Button(btn_box2, command=lambda: self.cmd_move_to_mon(1))
        self.btn_mon1.pack(side=tk.LEFT, padx=3)

        self.btn_mon2 = ttk.Button(btn_box2, command=lambda: self.cmd_move_to_mon(2))
        self.btn_mon2.pack(side=tk.LEFT, padx=3)

        self.btn_mon3 = ttk.Button(btn_box2, command=lambda: self.cmd_move_to_mon(3))
        self.btn_mon3.pack(side=tk.LEFT, padx=3)

        # Windows List Frame
        self.win_lf = ttk.LabelFrame(main_frame, padding=10)
        self.win_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        columns = ("title", "pos", "size", "hwnd")
        self.tree = ttk.Treeview(self.win_lf, columns=columns, show="headings", selectmode="browse")

        self.tree.column("title", width=400)
        self.tree.column("pos", width=130, anchor="center")
        self.tree.column("size", width=120, anchor="center")
        self.tree.column("hwnd", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(self.win_lf, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Double-click to move selected window to mouse cursor
        self.tree.bind("<Double-1>", lambda event: self.cmd_move_selected_to_cursor())

        # Bottom control bar
        bottom_bar = ttk.Frame(main_frame)
        bottom_bar.pack(fill=tk.X, pady=(5, 0))

        self.btn_refresh = ttk.Button(bottom_bar, command=self.refresh_all)
        self.btn_refresh.pack(side=tk.LEFT)

        self.btn_move_sel = ttk.Button(bottom_bar, command=self.cmd_move_selected_to_cursor)
        self.btn_move_sel.pack(side=tk.LEFT, padx=10)

        self.lbl_status_bar = ttk.Label(bottom_bar, font=("Segoe UI", 9, "italic"))
        self.lbl_status_bar.pack(side=tk.RIGHT)

    def on_language_change(self, lang_code):
        """Handles language change from menu or dropdown."""
        set_language(lang_code)
        self.lang_var.set(lang_code)
        self.combo_lang.set(LANGUAGES.get(lang_code, "English"))
        self.retranslate_ui()
        self.refresh_all()

    def _on_combobox_language_change(self, event=None):
        """Callback when user selects a language from the dropdown."""
        selected_name = self.combo_lang.get()
        for code, name in LANGUAGES.items():
            if name == selected_name:
                self.on_language_change(code)
                break

    def retranslate_ui(self):
        """Updates all interface labels and button texts based on active language."""
        self.root.title(t("app_window_title"))
        self.menu_bar.entryconfig(1, label=t("menu_language"))

        self.title_label.config(text=t("app_title"))
        self.subtitle_label.config(text=t("app_subtitle"))
        self.lbl_lang_select.config(text=t("lbl_language"))

        self.status_lf.config(text=t("status_frame_title"))
        self.actions_lf.config(text=t("actions_frame_title"))
        self.win_lf.config(text=t("windows_frame_title"))

        self.btn_cursor.config(text=t("btn_move_to_cursor"))
        self.btn_gather.config(text=t("btn_gather_offscreen"))
        self.lbl_mon_sel.config(text=t("lbl_move_active_to"))

        self.btn_mon1.config(text=t("btn_mon_1"))
        self.btn_mon2.config(text=t("btn_mon_2"))
        self.btn_mon3.config(text=t("btn_mon_3"))

        self.tree.heading("title", text=t("col_title"))
        self.tree.heading("pos", text=t("col_pos"))
        self.tree.heading("size", text=t("col_size"))
        self.tree.heading("hwnd", text=t("col_hwnd"))

        self.btn_refresh.config(text=t("btn_refresh"))
        self.btn_move_sel.config(text=t("btn_move_selected"))
        self.lbl_status_bar.config(text=t("status_ready"))

    def refresh_all(self):
        """Refreshes monitor info, mouse cursor position, active window, and open windows list."""
        monitors = get_monitors()
        mon_str = " | ".join([
            f"Monitor {i+1}{t('lbl_mon_primary') if m['primary'] else ''}: {m['work_width']}x{m['work_height']}"
            for i, m in enumerate(monitors)
        ])
        self.lbl_monitors.config(text=t("lbl_monitors_format", count=len(monitors), monitors=mon_str))

        # Cursor position
        idx, cur_mon = get_cursor_monitor_index(monitors)
        device_name = cur_mon['device'] if cur_mon else ''
        self.lbl_cursor.config(text=t("lbl_cursor_format", index=idx+1, device=device_name))

        # Active window
        active = get_active_window()
        if active and active['title'] and active['title'] != self.root.title():
            self.lbl_active.config(text=t("lbl_active_format", title=active['title'][:60]))
        else:
            self.lbl_active.config(text=t("lbl_active_none"))

        # Windows list
        for item in self.tree.get_children():
            self.tree.delete(item)

        windows = get_desktop_windows()
        for w in windows:
            l, t_pos, r, b = w['rect']
            pos_str = f"({l}, {t_pos})"
            if w.get('is_minimized'):
                pos_str += t("tag_minimized")
            elif w.get('is_maximized'):
                pos_str += t("tag_maximized")
            size_str = f"{w['width']} x {w['height']}"
            self.tree.insert("", tk.END, values=(w['title'], pos_str, size_str, w['hwnd']))

    def cmd_move_to_cursor(self):
        """Moves selected or active window to mouse cursor."""
        sel = self.tree.selection()
        if sel:
            self.cmd_move_selected_to_cursor()
            return

        res = move_active_to_cursor()
        if res:
            self.set_status(t("status_moved_to_cursor"))
        else:
            self.set_status(t("status_no_active_window"))
        self.root.after(300, self.refresh_all)

    def cmd_gather(self):
        """Gathers off-screen windows to primary display."""
        count = gather_offscreen_windows()
        self.set_status(t("status_gathered", count=count))
        self.root.after(300, self.refresh_all)

    def cmd_move_to_mon(self, idx):
        """Moves selected or active window to Monitor by 1-based index."""
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])
            try:
                hwnd = int(item['values'][3])
            except (ValueError, IndexError):
                hwnd = None
            monitors = get_monitors()
            if not monitors or not hwnd:
                return
            target_idx = max(0, min(idx - 1, len(monitors) - 1))
            target_mon = monitors[target_idx]
            res = move_window_to_monitor(hwnd, target_mon)
            if res:
                self.set_status(t("status_moved_selected", title=str(item['values'][0])[:30], index=target_idx + 1))
            else:
                self.set_status(t("status_move_failed"))
            self.root.after(300, self.refresh_all)
            return

        res = move_active_to_monitor_index(idx)
        if res:
            self.set_status(t("status_moved_to_mon", index=idx))
        else:
            self.set_status(t("status_move_failed"))
        self.root.after(300, self.refresh_all)

    def cmd_move_selected_to_cursor(self):
        """Moves window selected in Treeview to the screen containing the mouse cursor."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(t("dialog_info_title"), t("dialog_select_window_first"))
            return
        item = self.tree.item(sel[0])
        hwnd = int(item['values'][3])

        monitors = get_monitors()
        if not monitors:
            return
        idx, cur_mon = get_cursor_monitor_index(monitors)
        move_window_to_monitor(hwnd, cur_mon)
        self.set_status(t("status_moved_selected", title=item['values'][0][:30], index=idx+1))
        self.root.after(300, self.refresh_all)

    def set_status(self, text):
        """Updates status bar text."""
        self.lbl_status_bar.config(text=text)

    def _on_hotkey_triggered(self, hotkey_name):
        """Callback when a global hotkey is pressed."""
        self.root.after(0, lambda: self.set_status(t("status_hotkey_triggered", name=hotkey_name)))
        self.root.after(400, self.refresh_all)

    def on_closing(self):
        """Stops background hotkey thread and exits cleanly."""
        self.hotkey_mgr.stop()
        self.root.destroy()


# ============================================================================
# Section 6: Command Line Interface & Main Entry Point
# ============================================================================

def build_cli_parser():
    """Builds and returns the argparse CLI parser."""
    parser = argparse.ArgumentParser(
        description="Monitor Window Relocator - Multi-monitor off-screen window recovery utility."
    )
    parser.add_argument(
        "--gather",
        action="store_true",
        help="Scan and move all off-screen windows to the primary display and exit."
    )
    parser.add_argument(
        "--to-cursor",
        action="store_true",
        help="Move currently active foreground window to monitor under mouse cursor and exit."
    )
    parser.add_argument(
        "--mon",
        type=int,
        help="Move active foreground window to specified monitor number (e.g. 1, 2, 3) and exit."
    )
    parser.add_argument(
        "--lang",
        choices=["en", "pl"],
        help="Set application language ('en' for English, 'pl' for Polski)."
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Monitor Window Relocator v1.1"
    )
    return parser


def main():
    """Main application entry point."""
    ensure_input_desktop()
    parser = build_cli_parser()
    args, unknown = parser.parse_known_args()

    # Handle language override if provided
    if args.lang:
        set_language(args.lang)

    # CLI command: Gather off-screen windows
    if args.gather:
        count = gather_offscreen_windows()
        print(t("cli_gathered", count=count))
        sys.exit(0)

    # CLI command: Move active window to cursor
    if args.to_cursor:
        res = move_active_to_cursor()
        print(t("cli_moved_to_cursor") if res else t("cli_no_active_window"))
        sys.exit(0)

    # CLI command: Move active window to monitor index
    if args.mon is not None:
        if args.mon < 1:
            print(t("cli_invalid_mon", index=args.mon))
            sys.exit(1)
        res = move_active_to_monitor_index(args.mon)
        print(t("cli_moved_to_mon", index=args.mon) if res else t("cli_no_active_window"))
        sys.exit(0)

    # Launch GUI Application
    root = tk.Tk()
    app = WindowRelocatorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
