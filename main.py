import sys
import os
import tkinter as tk
import relocator_core
from app_gui import WindowRelocatorApp

def main():
    # Handle quick CLI flags
    if "--gather" in sys.argv:
        count = relocator_core.gather_offscreen_windows()
        print(f"Ściągnięto {count} niewidocznych okien na ekran główny.")
        sys.exit(0)

    if "--to-cursor" in sys.argv:
        res = relocator_core.move_active_to_cursor()
        print("Przeniesiono aktywne okno na monitor pod kursorem." if res else "Nie znaleziono aktywnego okna.")
        sys.exit(0)

    # Launch GUI Application
    root = tk.Tk()
    app = WindowRelocatorApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
