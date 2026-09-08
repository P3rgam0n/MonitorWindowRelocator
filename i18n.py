"""
Internationalization (i18n) module for Monitor Window Relocator.
Provides localization support with English as default and Polish as an alternative option.
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

LANGUAGES = {
    "en": "English",
    "pl": "Polski"
}

TRANSLATIONS = {
    "en": {
        # App Info
        "app_title": "🖥️ Monitor Window Relocator",
        "app_window_title": "Monitor Window Relocator v1.0",
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
        
        # CLI Output
        "cli_gathered": "Gathered {count} hidden window(s) to primary screen.",
        "cli_moved_to_cursor": "Moved active window to monitor under mouse cursor.",
        "cli_no_active_window": "No active window found.",
        
        # Logs
        "log_reg_failed": "[HotkeyManager] Failed to register hotkey: {name}",
        "log_action_error": "[HotkeyManager] Error executing action {name}: {error}",
        "log_unregistered": "[HotkeyManager] Successfully unregistered hotkeys."
    },
    "pl": {
        # App Info
        "app_title": "🖥️ Monitor Window Relocator",
        "app_window_title": "Monitor Window Relocator v1.0",
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
        
        # CLI Output
        "cli_gathered": "Ściągnięto {count} niewidocznych okien na ekran główny.",
        "cli_moved_to_cursor": "Przeniesiono aktywne okno na monitor pod kursorem.",
        "cli_no_active_window": "Nie znaleziono aktywnego okna.",
        
        # Logs
        "log_reg_failed": "[HotkeyManager] Nie udało się zarejestrować skrótu: {name}",
        "log_action_error": "[HotkeyManager] Błąd podczas wykonywania akcji {name}: {error}",
        "log_unregistered": "[HotkeyManager] Pomyślnie wyrejestrowano skróty klawiszowe."
    }
}

# Current default language is English ("en")
_current_lang = "en"


def load_config():
    """Load configuration including language preference from config.json."""
    global _current_lang
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language", "en")
                if lang in LANGUAGES:
                    _current_lang = lang
        except Exception:
            _current_lang = "en"


def save_config():
    """Save configuration including language preference to config.json."""
    try:
        data = {"language": _current_lang}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def set_language(lang_code):
    """Set active language code ('en' or 'pl') and save preference."""
    global _current_lang
    if lang_code in LANGUAGES:
        _current_lang = lang_code
        save_config()


def get_language():
    """Get currently active language code."""
    return _current_lang


def t(key, **kwargs):
    """Retrieve localized string for key in current language with optional formatting."""
    lang_dict = TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


# Initialize config on module import
load_config()
