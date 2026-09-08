import tkinter as tk
from tkinter import ttk, messagebox
import relocator_core
from hotkey_manager import HotkeyManager
from i18n import t, set_language, get_language, LANGUAGES


class WindowRelocatorApp:
    """Tkinter GUI Application for Monitor Window Relocator."""

    def __init__(self, root):
        self.root = root
        self.root.geometry("820x600")
        self.root.minsize(680, 500)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Background color configuration
        BG_COLOR = "#f4f6f9"
        self.root.configure(bg=BG_COLOR)

        self.hotkey_mgr = HotkeyManager(on_hotkey_triggered_callback=self._on_hotkey_triggered)
        self.hotkey_mgr.start()

        self._create_menu()
        self._create_widgets()
        self.retranslate_ui()
        self.refresh_all()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_menu(self):
        """Creates top menu bar with language settings."""
        self.menu_bar = tk.Menu(self.root)
        
        # Language Menu
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

        self.title_label = ttk.Label(
            title_sub_frame,
            font=("Segoe UI", 16, "bold")
        )
        self.title_label.pack(anchor="w", pady=(0, 2))

        self.subtitle_label = ttk.Label(
            title_sub_frame,
            font=("Segoe UI", 9, "italic")
        )
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
        # Select current language in combobox
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

        self.btn_cursor = ttk.Button(
            btn_box1,
            command=self.cmd_move_to_cursor
        )
        self.btn_cursor.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        self.btn_gather = ttk.Button(
            btn_box1,
            command=self.cmd_gather
        )
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

        # Treeview list
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
        """Handles language change from menu or combobox."""
        set_language(lang_code)
        self.lang_var.set(lang_code)
        self.combo_lang.set(LANGUAGES.get(lang_code, "English"))
        self.retranslate_ui()
        self.refresh_all()

    def _on_combobox_language_change(self, event=None):
        """Callback when user selects a language from the combobox."""
        selected_name = self.combo_lang.get()
        for code, name in LANGUAGES.items():
            if name == selected_name:
                self.on_language_change(code)
                break

    def retranslate_ui(self):
        """Updates all text strings in the interface based on current language."""
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
        """Refreshes active monitor information, cursor position, active window, and open windows list."""
        monitors = relocator_core.get_monitors()
        mon_str = " | ".join([
            f"Monitor {i+1}{t('lbl_mon_primary') if m['primary'] else ''}: {m['work_width']}x{m['work_height']}"
            for i, m in enumerate(monitors)
        ])
        self.lbl_monitors.config(text=t("lbl_monitors_format", count=len(monitors), monitors=mon_str))

        # Refresh Cursor Position
        idx, cur_mon = relocator_core.get_cursor_monitor_index(monitors)
        device_name = cur_mon['device'] if cur_mon else ''
        self.lbl_cursor.config(text=t("lbl_cursor_format", index=idx+1, device=device_name))

        # Refresh Active Window
        active = relocator_core.get_active_window()
        if active and active['title'] and active['title'] != self.root.title():
            self.lbl_active.config(text=t("lbl_active_format", title=active['title'][:60]))
        else:
            self.lbl_active.config(text=t("lbl_active_none"))

        # Refresh Open Windows Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        windows = relocator_core.get_desktop_windows()
        for w in windows:
            l, t_pos, r, b = w['rect']
            pos_str = f"({l}, {t_pos})"
            size_str = f"{w['width']} x {w['height']}"
            self.tree.insert("", tk.END, values=(w['title'], pos_str, size_str, w['hwnd']))

    def cmd_move_to_cursor(self):
        """Action for moving active window to mouse cursor."""
        res = relocator_core.move_active_to_cursor()
        if res:
            self.set_status(t("status_moved_to_cursor"))
        else:
            self.set_status(t("status_no_active_window"))
        self.root.after(300, self.refresh_all)

    def cmd_gather(self):
        """Action for gathering hidden off-screen windows to primary display."""
        count = relocator_core.gather_offscreen_windows()
        self.set_status(t("status_gathered", count=count))
        self.root.after(300, self.refresh_all)

    def cmd_move_to_mon(self, idx):
        """Action for moving active window to Monitor 1, 2, or 3."""
        res = relocator_core.move_active_to_monitor_index(idx)
        if res:
            self.set_status(t("status_moved_to_mon", index=idx))
        else:
            self.set_status(t("status_move_failed"))
        self.root.after(300, self.refresh_all)

    def cmd_move_selected_to_cursor(self):
        """Action for moving window selected in Treeview to mouse cursor monitor."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(t("dialog_info_title"), t("dialog_select_window_first"))
            return
        item = self.tree.item(sel[0])
        hwnd = int(item['values'][3])

        monitors = relocator_core.get_monitors()
        if not monitors:
            return
        idx, cur_mon = relocator_core.get_cursor_monitor_index(monitors)
        relocator_core.move_window_to_monitor(hwnd, cur_mon)
        self.set_status(t("status_moved_selected", title=item['values'][0][:30], index=idx+1))
        self.root.after(300, self.refresh_all)

    def set_status(self, text):
        """Updates status bar message."""
        self.lbl_status_bar.config(text=text)

    def _on_hotkey_triggered(self, hotkey_name):
        """Callback when a global hotkey is pressed."""
        self.root.after(0, lambda: self.set_status(t("status_hotkey_triggered", name=hotkey_name)))
        self.root.after(400, self.refresh_all)

    def on_closing(self):
        """Stops background threads and destroys window on exit."""
        self.hotkey_mgr.stop()
        self.root.destroy()
