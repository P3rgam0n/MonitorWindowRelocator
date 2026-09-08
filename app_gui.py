import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import relocator_core
from hotkey_manager import HotkeyManager

class WindowRelocatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor Window Relocator v1.0")
        self.root.geometry("780x560")
        self.root.minsize(650, 480)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors & Padding
        BG_COLOR = "#f4f6f9"
        self.root.configure(bg=BG_COLOR)

        self.hotkey_mgr = HotkeyManager(on_hotkey_triggered_callback=self._on_hotkey_triggered)
        self.hotkey_mgr.start()

        self._create_widgets()
        self.refresh_all()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title / Header
        title_label = ttk.Label(
            main_frame,
            text="🖥️ Monitor Window Relocator",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(anchor="w", pady=(0, 5))

        subtitle_label = ttk.Label(
            main_frame,
            text="Szybkie przenoszenie okien z wyłączonych / uśpionych monitorów na aktywny ekran.",
            font=("Segoe UI", 9, "italic")
        )
        subtitle_label.pack(anchor="w", pady=(0, 10))

        # Status Frame
        status_lf = ttk.LabelFrame(main_frame, text=" Monitor & System Status ", padding=10)
        status_lf.pack(fill=tk.X, pady=(0, 10))

        self.lbl_monitors = ttk.Label(status_lf, text="Wykryte monitory: wczytywanie...", font=("Segoe UI", 9))
        self.lbl_monitors.pack(anchor="w", pady=2)

        self.lbl_cursor = ttk.Label(status_lf, text="Kursor myszy: wczytywanie...", font=("Segoe UI", 9))
        self.lbl_cursor.pack(anchor="w", pady=2)

        self.lbl_active = ttk.Label(status_lf, text="Aktywne okno: brak", font=("Segoe UI", 9, "bold"))
        self.lbl_active.pack(anchor="w", pady=2)

        # Quick Actions Frame
        actions_lf = ttk.LabelFrame(main_frame, text=" Szybkie Akcje & Skróty Klawiszowe ", padding=10)
        actions_lf.pack(fill=tk.X, pady=(0, 10))

        btn_box1 = ttk.Frame(actions_lf)
        btn_box1.pack(fill=tk.X, pady=2)

        btn_cursor = ttk.Button(
            btn_box1,
            text="🎯 Przenieś aktywne okno do myszy (Ctrl+Alt+M)",
            command=self.cmd_move_to_cursor
        )
        btn_cursor.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        btn_gather = ttk.Button(
            btn_box1,
            text="🧹 Ściągnij ukryte okna na Ekran Główny (Ctrl+Alt+G)",
            command=self.cmd_gather
        )
        btn_gather.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_box2 = ttk.Frame(actions_lf)
        btn_box2.pack(fill=tk.X, pady=(6, 0))

        lbl_mon_sel = ttk.Label(btn_box2, text="Przenieś aktywne okno na:", font=("Segoe UI", 9, "bold"))
        lbl_mon_sel.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_mon1 = ttk.Button(btn_box2, text="Monitor 1 (Ctrl+Alt+1)", command=lambda: self.cmd_move_to_mon(1))
        self.btn_mon1.pack(side=tk.LEFT, padx=3)

        self.btn_mon2 = ttk.Button(btn_box2, text="Monitor 2 (Ctrl+Alt+2)", command=lambda: self.cmd_move_to_mon(2))
        self.btn_mon2.pack(side=tk.LEFT, padx=3)

        self.btn_mon3 = ttk.Button(btn_box2, text="Monitor 3 (Ctrl+Alt+3)", command=lambda: self.cmd_move_to_mon(3))
        self.btn_mon3.pack(side=tk.LEFT, padx=3)

        # Windows List Frame
        win_lf = ttk.LabelFrame(main_frame, text=" Otwarte Aplikacje i Okna ", padding=10)
        win_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Treeview list
        columns = ("title", "pos", "size", "hwnd")
        self.tree = ttk.Treeview(win_lf, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("title", text="Tytuł Okna")
        self.tree.heading("pos", text="Współrzędne (X, Y)")
        self.tree.heading("size", text="Rozmiar (W x H)")
        self.tree.heading("hwnd", text="HWND")

        self.tree.column("title", width=380)
        self.tree.column("pos", width=120, anchor="center")
        self.tree.column("size", width=110, anchor="center")
        self.tree.column("hwnd", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(win_lf, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom control bar
        bottom_bar = ttk.Frame(main_frame)
        bottom_bar.pack(fill=tk.X, pady=(5, 0))

        btn_refresh = ttk.Button(bottom_bar, text="🔄 Odśwież listę okien", command=self.refresh_all)
        btn_refresh.pack(side=tk.LEFT)

        btn_move_sel = ttk.Button(bottom_bar, text="🎯 Przenieś zaznaczone okno do myszy", command=self.cmd_move_selected_to_cursor)
        btn_move_sel.pack(side=tk.LEFT, padx=10)

        self.lbl_status_bar = ttk.Label(bottom_bar, text="Gotowy", font=("Segoe UI", 9, "italic"))
        self.lbl_status_bar.pack(side=tk.RIGHT)

    def refresh_all(self):
        # Refresh Monitors
        monitors = relocator_core.get_monitors()
        mon_str = " | ".join([
            f"Monitor {i+1}{' (Główny)' if m['primary'] else ''}: {m['work_width']}x{m['work_height']}"
            for i, m in enumerate(monitors)
        ])
        self.lbl_monitors.config(text=f"Wykryte monitory ({len(monitors)}): {mon_str}")

        # Refresh Cursor
        idx, cur_mon = relocator_core.get_cursor_monitor_index(monitors)
        self.lbl_cursor.config(text=f"Kursor myszy znajduje się na: Monitor {idx+1} ({cur_mon['device'] if cur_mon else ''})")

        # Refresh Active window
        active = relocator_core.get_active_window()
        if active and active['title'] and active['title'] != self.root.title():
            self.lbl_active.config(text=f"Aktywne okno: '{active['title'][:60]}'")
        else:
            self.lbl_active.config(text="Aktywne okno: Monitor Window Relocator (lub brak)")

        # Refresh Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        windows = relocator_core.get_desktop_windows()
        for w in windows:
            l, t, r, b = w['rect']
            pos_str = f"({l}, {t})"
            size_str = f"{w['width']} x {w['height']}"
            self.tree.insert("", tk.END, values=(w['title'], pos_str, size_str, w['hwnd']))

    def cmd_move_to_cursor(self):
        res = relocator_core.move_active_to_cursor()
        if res:
            self.set_status("Przeniesiono aktywne okno na ekran z kursorem myszy.")
        else:
            self.set_status("Brak aktywnego okna do przeniesienia.")
        self.root.after(300, self.refresh_all)

    def cmd_gather(self):
        count = relocator_core.gather_offscreen_windows()
        self.set_status(f"Ściągnięto {count} niewidocznych okien na ekran główny.")
        self.root.after(300, self.refresh_all)

    def cmd_move_to_mon(self, idx):
        res = relocator_core.move_active_to_monitor_index(idx)
        if res:
            self.set_status(f"Przeniesiono aktywne okno na Monitor {idx}.")
        else:
            self.set_status("Nie udało się przenieść okna.")
        self.root.after(300, self.refresh_all)

    def cmd_move_selected_to_cursor(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Informacja", "Zaznacz najpierw okno z listy otwartych aplikacji.")
            return
        item = self.tree.item(sel[0])
        hwnd = int(item['values'][3])
        
        monitors = relocator_core.get_monitors()
        if not monitors:
            return
        idx, cur_mon = relocator_core.get_cursor_monitor_index(monitors)
        relocator_core.move_window_to_monitor(hwnd, cur_mon)
        self.set_status(f"Przeniesiono '{item['values'][0][:30]}' na Monitor {idx+1}.")
        self.root.after(300, self.refresh_all)

    def set_status(self, text):
        self.lbl_status_bar.config(text=text)

    def _on_hotkey_triggered(self, hotkey_name):
        self.root.after(0, lambda: self.set_status(f"Uruchomiono skrót: {hotkey_name}"))
        self.root.after(400, self.refresh_all)

    def on_closing(self):
        self.hotkey_mgr.stop()
        self.root.destroy()
