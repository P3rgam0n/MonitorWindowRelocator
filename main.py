import sys
import os
import tkinter as tk
import relocator_core
from app_gui import WindowRelocatorApp
from i18n import t, set_language


def main():
    """Main entry point for Monitor Window Relocator."""

    # Handle CLI language flag override (--lang en / --lang pl)
    if "--lang" in sys.argv:
        try:
            lang_idx = sys.argv.index("--lang") + 1
            if lang_idx < len(sys.argv):
                set_language(sys.argv[lang_idx])
        except Exception:
            pass

    # Handle quick CLI flags
    if "--gather" in sys.argv:
        count = relocator_core.gather_offscreen_windows()
        print(t("cli_gathered", count=count))
        sys.exit(0)

    if "--to-cursor" in sys.argv:
        res = relocator_core.move_active_to_cursor()
        print(t("cli_moved_to_cursor") if res else t("cli_no_active_window"))
        sys.exit(0)

    # Launch GUI Application
    root = tk.Tk()
    app = WindowRelocatorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
