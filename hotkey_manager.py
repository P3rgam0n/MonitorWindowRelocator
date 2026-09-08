import ctypes
from ctypes import wintypes
import threading
import time
import relocator_core

user32 = ctypes.windll.user32

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

VK_M = 0x4D
VK_G = 0x47
VK_1 = 0x31
VK_2 = 0x32
VK_3 = 0x33

class HotkeyManager:
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
        relocator_core.move_active_to_cursor()

    def _action_gather(self):
        relocator_core.gather_offscreen_windows()

    def _action_move_mon(self, idx):
        relocator_core.move_active_to_monitor_index(idx)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _run_loop(self):
        registered = []
        for hk_id, mods, vk, name, action in self.hotkeys:
            if user32.RegisterHotKey(None, hk_id, mods, vk):
                registered.append(hk_id)
            else:
                print(f"[HotkeyManager] Nie udało się zarejestrować skrótu: {name}")

        msg = wintypes.MSG()
        try:
            while self.running:
                # PeekMessage to allow non-blocking exit check
                if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1): # PM_REMOVE = 1
                    if msg.message == WM_HOTKEY:
                        hk_id = msg.wParam
                        for id_val, mods, vk, name, action in self.hotkeys:
                            if id_val == hk_id:
                                try:
                                    action()
                                    if self.callback:
                                        self.callback(name)
                                except Exception as e:
                                    print(f"[HotkeyManager] Błąd podczas wykonywania akcji {name}: {e}")
                                break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    time.sleep(0.05)
        finally:
            for hk_id in registered:
                user32.UnregisterHotKey(None, hk_id)
            print("[HotkeyManager] Pomyślnie wyrejestrowano skróty klawiszowe.")
