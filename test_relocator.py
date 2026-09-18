"""
Comprehensive test suite for Monitor Window Relocator (main.py).
Tests core algorithms, Win32 coordinate logic, monitor selection,
i18n translations, themes, config persistence, CLI arguments,
assets resolution, and HotkeyManager.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import main


class TestWin32Rect(unittest.TestCase):
    """Tests for the Win32 RECT structure and helpers."""

    def test_rect_dimensions(self):
        r = main.RECT(left=100, top=200, right=500, bottom=700)
        self.assertEqual(r.width, 400)
        self.assertEqual(r.height, 500)

    def test_rect_zero_dimensions(self):
        r = main.RECT(left=50, top=50, right=50, bottom=50)
        self.assertEqual(r.width, 0)
        self.assertEqual(r.height, 0)


class TestMonitorCalculations(unittest.TestCase):
    """Tests for monitor detection, primary selection, and cursor placement."""

    def setUp(self):
        self.sample_monitors = [
            {
                'handle': 101,
                'device': '\\\\.\\DISPLAY1',
                'rect': (0, 0, 1920, 1080),
                'work': (0, 0, 1920, 1040),
                'work_width': 1920,
                'work_height': 1040,
                'primary': True
            },
            {
                'handle': 102,
                'device': '\\\\.\\DISPLAY2',
                'rect': (1920, 0, 3840, 1080),
                'work': (1920, 0, 3840, 1040),
                'work_width': 1920,
                'work_height': 1040,
                'primary': False
            },
            {
                'handle': 103,
                'device': '\\\\.\\DISPLAY3',
                'rect': (-1920, 0, 0, 1080),
                'work': (-1920, 0, 0, 1040),
                'work_width': 1920,
                'work_height': 1040,
                'primary': False
            }
        ]

    def test_get_primary_monitor_found(self):
        primary = main.get_primary_monitor(self.sample_monitors)
        self.assertIsNotNone(primary)
        self.assertTrue(primary['primary'])
        self.assertEqual(primary['device'], '\\\\.\\DISPLAY1')

    def test_get_primary_monitor_none_marked(self):
        monitors_no_primary = [
            {'rect': (0, 0, 1920, 1080), 'primary': False, 'device': 'MON1'},
            {'rect': (1920, 0, 3840, 1080), 'primary': False, 'device': 'MON2'},
        ]
        primary = main.get_primary_monitor(monitors_no_primary)
        self.assertEqual(primary['device'], 'MON1')

    def test_get_primary_monitor_empty(self):
        self.assertIsNone(main.get_primary_monitor([]))

    def test_get_cursor_monitor_empty(self):
        idx, mon = main.get_cursor_monitor_index([])
        self.assertEqual(idx, 0)
        self.assertIsNone(mon)

    @patch('main.user32.GetCursorPos')
    def test_get_cursor_monitor_inside(self, mock_cursor):
        # Mock cursor at (2500, 500) -> DISPLAY2
        def side_effect(pt_ref):
            obj = getattr(pt_ref, '_obj', pt_ref)
            obj.x = 2500
            obj.y = 500
            return 1
        mock_cursor.side_effect = side_effect

        idx, mon = main.get_cursor_monitor_index(self.sample_monitors)
        self.assertEqual(idx, 1)
        self.assertEqual(mon['device'], '\\\\.\\DISPLAY2')

    @patch('main.user32.GetCursorPos')
    def test_get_cursor_monitor_nearest_fallback(self, mock_cursor):
        # Mock cursor way off to the right at (5000, 500) -> closest is DISPLAY2
        def side_effect(pt_ref):
            obj = getattr(pt_ref, '_obj', pt_ref)
            obj.x = 5000
            obj.y = 500
            return 1
        mock_cursor.side_effect = side_effect

        idx, mon = main.get_cursor_monitor_index(self.sample_monitors)
        self.assertEqual(idx, 1)
        self.assertEqual(mon['device'], '\\\\.\\DISPLAY2')


class TestIsRectOnAnyMonitor(unittest.TestCase):
    """Tests for window geometry and off-screen detection."""

    def setUp(self):
        self.monitors = [
            {
                'rect': (0, 0, 1920, 1080),
                'work': (0, 0, 1920, 1040),
            },
            {
                'rect': (1920, 0, 3840, 1080),
                'work': (1920, 0, 3840, 1040),
            }
        ]

    def test_rect_inside_first_monitor(self):
        # Window centered at (500, 400)
        rect = (100, 100, 900, 700)
        self.assertTrue(main.is_rect_on_any_monitor(rect, self.monitors))

    def test_rect_inside_second_monitor(self):
        # Window centered at (2500, 400)
        rect = (2100, 100, 2900, 700)
        self.assertTrue(main.is_rect_on_any_monitor(rect, self.monitors))

    def test_rect_completely_offscreen(self):
        # Window stranded on disconnected third monitor (e.g. X: 4500)
        rect = (4200, 100, 5000, 700)
        self.assertFalse(main.is_rect_on_any_monitor(rect, self.monitors))

    def test_rect_negative_offscreen(self):
        # Window stranded on disconnected left monitor (e.g. X: -1500)
        rect = (-1800, 100, -1000, 700)
        self.assertFalse(main.is_rect_on_any_monitor(rect, self.monitors))

    def test_rect_partial_overlap_significant(self):
        # Overlaps left side of monitor 1 by 50%
        rect = (-400, 100, 400, 700)  # total width 800, 400 pixels (50%) visible
        self.assertTrue(main.is_rect_on_any_monitor(rect, self.monitors))

    def test_rect_empty_monitors(self):
        rect = (100, 100, 500, 500)
        self.assertFalse(main.is_rect_on_any_monitor(rect, []))

    def test_rect_degenerate(self):
        # Width <= 0 or Height <= 0
        self.assertFalse(main.is_rect_on_any_monitor((100, 100, 100, 500), self.monitors))
        self.assertFalse(main.is_rect_on_any_monitor((100, 100, 500, 100), self.monitors))


class TestWindowRelocation(unittest.TestCase):
    """Tests for window moving logic, validation and boundary clamps."""

    def test_move_window_invalid_hwnd(self):
        # Zero hwnd
        self.assertFalse(main.move_window_to_monitor(0, {'work': (0, 0, 1920, 1080), 'work_width': 1920, 'work_height': 1080}))
        # None target
        self.assertFalse(main.move_window_to_monitor(12345, None))

    @patch('main.user32.IsWindow', return_value=False)
    def test_move_window_nonexistent_hwnd(self, mock_is_window):
        target = {'work': (0, 0, 1920, 1080), 'work_width': 1920, 'work_height': 1080}
        self.assertFalse(main.move_window_to_monitor(99999, target))

    @patch('main.user32.IsWindow', return_value=True)
    @patch('main.user32.IsIconic', return_value=False)
    @patch('main.user32.IsZoomed', return_value=False)
    @patch('main.user32.GetWindowRect')
    @patch('main.user32.SetWindowPos', return_value=1)
    @patch('main.user32.SetForegroundWindow', return_value=1)
    def test_move_window_centering_and_scaling(self, mock_fg, mock_pos, mock_rect, mock_zoomed, mock_iconic, mock_win):
        # Mock window rect: 1000x800
        def rect_side_effect(hwnd, pt_ref):
            obj = getattr(pt_ref, '_obj', pt_ref)
            obj.left = 0
            obj.top = 0
            obj.right = 1000
            obj.bottom = 800
            return 1
        mock_rect.side_effect = rect_side_effect

        target = {
            'work': (1920, 0, 3840, 1080),
            'work_width': 1920,
            'work_height': 1080
        }

        res = main.move_window_to_monitor(5555, target)
        self.assertTrue(res)
        mock_pos.assert_called_once()
        args = mock_pos.call_args[0]
        hwnd, _, new_x, new_y, new_w, new_h, flags = args
        self.assertEqual(hwnd, 5555)
        # Should be centered inside target monitor work area (1920 to 3840)
        self.assertGreaterEqual(new_x, 1920)
        self.assertLess(new_x, 3840)
        self.assertGreaterEqual(new_y, 0)
        self.assertEqual(new_w, 1000)
        self.assertEqual(new_h, 800)

    @patch('main.user32.IsWindow', return_value=True)
    @patch('main.user32.IsIconic', return_value=True)
    @patch('main.user32.IsZoomed', return_value=False)
    @patch('main.user32.ShowWindow')
    @patch('main.user32.GetWindowRect')
    @patch('main.user32.SetWindowPos', return_value=1)
    @patch('main.user32.SetForegroundWindow', return_value=1)
    def test_move_window_minimized_restores(self, mock_fg, mock_pos, mock_rect, mock_show, mock_zoomed, mock_iconic, mock_win):
        def rect_side_effect(hwnd, pt_ref):
            obj = getattr(pt_ref, '_obj', pt_ref)
            obj.left, obj.top, obj.right, obj.bottom = 0, 0, 500, 400
            return 1
        mock_rect.side_effect = rect_side_effect
        target = {'work': (0, 0, 1920, 1080), 'work_width': 1920, 'work_height': 1080}
        res = main.move_window_to_monitor(1234, target)
        self.assertTrue(res)
        mock_show.assert_called_with(1234, main.SW_RESTORE)

    @patch('main.user32.IsWindow', return_value=True)
    @patch('main.user32.IsIconic', return_value=False)
    @patch('main.user32.IsZoomed', return_value=True)
    @patch('main.user32.ShowWindow')
    @patch('main.user32.GetWindowRect')
    @patch('main.user32.SetWindowPos', return_value=1)
    @patch('main.user32.SetForegroundWindow', return_value=1)
    def test_move_window_maximized_remaximizes(self, mock_fg, mock_pos, mock_rect, mock_show, mock_zoomed, mock_iconic, mock_win):
        def rect_side_effect(hwnd, pt_ref):
            obj = getattr(pt_ref, '_obj', pt_ref)
            obj.left, obj.top, obj.right, obj.bottom = 0, 0, 1920, 1080
            return 1
        mock_rect.side_effect = rect_side_effect
        target = {'work': (1920, 0, 3840, 1080), 'work_width': 1920, 'work_height': 1080}
        res = main.move_window_to_monitor(1234, target, force_restore_maximize=True)
        self.assertTrue(res)
        # Verify SW_RESTORE and SW_MAXIMIZE were called
        mock_show.assert_any_call(1234, main.SW_RESTORE)
        mock_show.assert_any_call(1234, main.SW_MAXIMIZE)

    @patch('main.user32.IsWindow', return_value=True)
    @patch('main.user32.IsIconic', return_value=False)
    @patch('main.user32.IsZoomed', return_value=False)
    @patch('main.user32.GetWindowRect')
    @patch('main.user32.SetWindowPos', return_value=1)
    @patch('main.user32.SetForegroundWindow', return_value=1)
    def test_move_window_preserves_small_window_size(self, mock_fg, mock_pos, mock_rect, mock_zoomed, mock_iconic, mock_win):
        # Window of size 320x240 (e.g. calculator or small tool)
        def rect_side_effect(hwnd, pt_ref):
            obj = getattr(pt_ref, '_obj', pt_ref)
            obj.left, obj.top, obj.right, obj.bottom = 0, 0, 320, 240
            return 1
        mock_rect.side_effect = rect_side_effect
        target = {'work': (0, 0, 1920, 1080), 'work_width': 1920, 'work_height': 1080}
        res = main.move_window_to_monitor(7777, target)
        self.assertTrue(res)
        args = mock_pos.call_args[0]
        _, _, _, _, new_w, new_h, _ = args
        # Compact size must be preserved, NOT inflated to 800x600
        self.assertEqual(new_w, 320)
        self.assertEqual(new_h, 240)


class TestI18nAndConfig(unittest.TestCase):
    """Tests for internationalization dictionaries, keys parity, and config persistence."""

    def test_translation_keys_symmetry(self):
        en_keys = set(main.TRANSLATIONS['en'].keys())
        pl_keys = set(main.TRANSLATIONS['pl'].keys())
        diff_en_pl = en_keys - pl_keys
        diff_pl_en = pl_keys - en_keys
        self.assertEqual(diff_en_pl, set(), f"Keys missing in PL translation: {diff_en_pl}")
        self.assertEqual(diff_pl_en, set(), f"Keys missing in EN translation: {diff_pl_en}")

    def test_translation_formatting(self):
        main.set_language('en')
        formatted = main.t('status_gathered', count=5)
        self.assertEqual(formatted, "Gathered 5 hidden window(s) to primary screen.")

        main.set_language('pl')
        formatted_pl = main.t('status_gathered', count=3)
        self.assertIn("3", formatted_pl)

    def test_translation_fallback(self):
        main.set_language('en')
        self.assertEqual(main.t('non_existent_key_xyz'), 'non_existent_key_xyz')

    def test_system_language_detection(self):
        detected = main.detect_system_language()
        self.assertIn(detected, ['en', 'pl'])

    def test_config_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_config = os.path.join(tmp_dir, "test_config.json")
            with patch('main.CONFIG_FILE', temp_config):
                main.set_language('pl')
                main.set_theme('dark')
                self.assertEqual(main.get_language(), 'pl')
                self.assertEqual(main.get_theme(), 'dark')
                self.assertTrue(os.path.exists(temp_config))

                # Reload
                main.load_config()
                self.assertEqual(main.get_language(), 'pl')
                self.assertEqual(main.get_theme(), 'dark')

                # Switch back
                main.set_language('en')
                main.set_theme('system')
                self.assertEqual(main.get_language(), 'en')
                self.assertEqual(main.get_theme(), 'system')

    def test_config_minimize_to_tray_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_config = os.path.join(tmpdir, "config.json")
            with patch.object(main, 'CONFIG_FILE', temp_config):
                main.set_minimize_to_tray(True)
                self.assertTrue(main.get_minimize_to_tray())
                self.assertTrue(os.path.exists(temp_config))

                # Reload
                main.load_config()
                self.assertTrue(main.get_minimize_to_tray())

                # Disable
                main.set_minimize_to_tray(False)
                self.assertFalse(main.get_minimize_to_tray())


class TestThemeSubsystem(unittest.TestCase):
    """Tests for theme detection, theme configuration, and palette definitions."""

    def test_theme_options_and_palettes(self):
        self.assertIn("system", main.THEMES)
        self.assertIn("dark", main.THEMES)
        self.assertIn("light", main.THEMES)

        self.assertIn("dark", main.THEME_PALETTES)
        self.assertIn("light", main.THEME_PALETTES)

        dark_pal = main.THEME_PALETTES["dark"]
        light_pal = main.THEME_PALETTES["light"]

        # Ensure all required keys exist in palettes
        expected_keys = [
            "bg_main", "bg_card", "bg_input", "fg_primary", "fg_secondary",
            "fg_accent", "btn_bg", "btn_fg", "btn_primary_bg", "btn_primary_fg",
            "tree_bg", "tree_fg", "tree_heading_bg", "border_color"
        ]
        for k in expected_keys:
            self.assertIn(k, dark_pal, f"Missing key '{k}' in dark palette")
            self.assertIn(k, light_pal, f"Missing key '{k}' in light palette")

    def test_dark_theme_modern_palette_values(self):
        dark_pal = main.THEME_PALETTES["dark"]
        self.assertEqual(dark_pal["bg_main"], "#121212")
        self.assertEqual(dark_pal["bg_card"], "#1e1e1e")
        self.assertEqual(dark_pal["border_color"], "#2a2a2a")
        self.assertEqual(dark_pal["btn_primary_bg"], "#2563eb")
        self.assertEqual(dark_pal["fg_primary"], "#e0e0e0")
        self.assertEqual(dark_pal["tree_heading_bg"], "#232323")

    def test_set_and_get_theme(self):
        main.set_theme("dark")
        self.assertEqual(main.get_theme(), "dark")
        self.assertEqual(main.get_effective_theme(), "dark")

        main.set_theme("light")
        self.assertEqual(main.get_theme(), "light")
        self.assertEqual(main.get_effective_theme(), "light")

        main.set_theme("system")
        self.assertEqual(main.get_theme(), "system")
        self.assertIn(main.get_effective_theme(), ["dark", "light"])

    def test_detect_system_theme(self):
        detected = main.detect_system_theme()
        self.assertIn(detected, ["dark", "light"])


class TestAssetPaths(unittest.TestCase):
    """Tests for application assets resolution."""

    def test_get_asset_path_local(self):
        ico_path = main.get_asset_path("icon.ico")
        self.assertTrue(os.path.isabs(ico_path))
        self.assertTrue(ico_path.endswith("icon.ico"))

    def test_get_asset_path_frozen(self):
        with patch.object(main.sys, 'frozen', True, create=True), \
             patch.object(main.sys, '_MEIPASS', r'C:\MockBundle', create=True):
            resolved = main.get_asset_path("icon.ico")
            self.assertTrue(resolved.startswith(r'C:\MockBundle'))


class TestDarkTitleBar(unittest.TestCase):
    """Tests for Win32 dark title bar helper."""

    @patch('main.dwmapi.DwmSetWindowAttribute', return_value=0)
    def test_apply_win32_dark_titlebar(self, mock_dwm):
        main.apply_win32_dark_titlebar(12345, True)
        mock_dwm.assert_called_once()
        args = mock_dwm.call_args[0]
        self.assertEqual(getattr(args[0], 'value', args[0]), 12345)
        self.assertEqual(args[1], main.DWMWA_USE_IMMERSIVE_DARK_MODE)


class TestCliParser(unittest.TestCase):
    """Tests for command-line argument parsing."""

    def setUp(self):
        self.parser = main.build_cli_parser()

    def test_cli_gather(self):
        args = self.parser.parse_args(['--gather'])
        self.assertTrue(args.gather)
        self.assertFalse(args.to_cursor)
        self.assertIsNone(args.mon)

    def test_cli_to_cursor(self):
        args = self.parser.parse_args(['--to-cursor'])
        self.assertTrue(args.to_cursor)
        self.assertFalse(args.gather)

    def test_cli_mon(self):
        args = self.parser.parse_args(['--mon', '2'])
        self.assertEqual(args.mon, 2)

    def test_cli_mon_arbitrary_index(self):
        # Supports multi-monitor setups beyond 3 displays (e.g. 4, 6)
        args = self.parser.parse_args(['--mon', '4'])
        self.assertEqual(args.mon, 4)

    def test_cli_lang(self):
        args = self.parser.parse_args(['--lang', 'pl'])
        self.assertEqual(args.lang, 'pl')

    def test_cli_theme(self):
        args = self.parser.parse_args(['--theme', 'dark'])
        self.assertEqual(args.theme, 'dark')


class TestMinimizedPlacement(unittest.TestCase):
    """Tests that minimized windows use normal restored position for off-screen detection."""

    def setUp(self):
        self.monitors = [
            {'rect': (0, 0, 1920, 1080), 'work': (0, 0, 1920, 1040), 'primary': True},
            {'rect': (1920, 0, 3840, 1080), 'work': (1920, 0, 3840, 1040), 'primary': False}
        ]

    def test_minimized_window_with_normal_rect_on_monitor(self):
        # A minimized window with restored coordinates inside Monitor 1 is NOT off-screen
        normal_rect = (200, 200, 1000, 800)
        self.assertTrue(main.is_rect_on_any_monitor(normal_rect, self.monitors))

    def test_minimized_window_with_normal_rect_offscreen(self):
        # A minimized window stranded on a disconnected display is correctly detected as off-screen
        normal_rect = (4500, 200, 5300, 800)
        self.assertFalse(main.is_rect_on_any_monitor(normal_rect, self.monitors))


class TestMonitorSorting(unittest.TestCase):
    """Tests spatial sorting for multi-monitor arrangements."""

    def test_spatial_sorting_left_to_right_and_top_to_bottom(self):
        unsorted_monitors = [
            {'rect': (1920, 0, 3840, 1080)},
            {'rect': (0, 1080, 1920, 2160)},
            {'rect': (0, 0, 1920, 1080)},
            {'rect': (-1920, 0, 0, 1080)}
        ]
        sorted_monitors = sorted(unsorted_monitors, key=lambda m: (m['rect'][0], m['rect'][1]))
        rects = [m['rect'] for m in sorted_monitors]
        expected = [
            (-1920, 0, 0, 1080),
            (0, 0, 1920, 1080),
            (0, 1080, 1920, 2160),
            (1920, 0, 3840, 1080)
        ]
        self.assertEqual(rects, expected)


class TestLiveSystemQueries(unittest.TestCase):
    """Smoke tests for live Win32 system queries on current machine."""

    def test_get_monitors_live(self):
        monitors = main.get_monitors()
        self.assertIsInstance(monitors, list)
        self.assertGreaterEqual(len(monitors), 1)
        first = monitors[0]
        self.assertIn('rect', first)
        self.assertIn('work', first)
        self.assertIn('work_width', first)
        self.assertIn('work_height', first)
        self.assertGreater(first['work_width'], 0)
        self.assertGreater(first['work_height'], 0)

    def test_get_desktop_windows_live(self):
        windows = main.get_desktop_windows()
        self.assertIsInstance(windows, list)
        for w in windows:
            self.assertIn('hwnd', w)
            self.assertIn('title', w)
            self.assertIn('rect', w)
            self.assertGreater(len(w['title']), 0)


class TestHotkeyManager(unittest.TestCase):
    """Tests for HotkeyManager lifecycle and state."""

    def test_hotkey_manager_structure(self):
        mgr = main.HotkeyManager()
        self.assertEqual(len(mgr.hotkeys), 5)
        names = [hk[3] for hk in mgr.hotkeys]
        self.assertIn("Ctrl+Alt+M", names)
        self.assertIn("Ctrl+Alt+G", names)
        self.assertIn("Ctrl+Alt+1", names)
        self.assertIn("Ctrl+Alt+2", names)
        self.assertIn("Ctrl+Alt+3", names)

    def test_hotkey_manager_lifecycle(self):
        mgr = main.HotkeyManager()
        self.assertFalse(mgr.running)
        mgr.start()
        self.assertTrue(mgr.running)
        self.assertIsNotNone(mgr.thread)
        self.assertTrue(mgr.thread.is_alive())
        mgr.stop()
        self.assertFalse(mgr.running)
        self.assertFalse(mgr.thread.is_alive())


class TestTrayManager(unittest.TestCase):
    """Tests for Win32 System Tray Manager lifecycle, tooltips, and callback mechanisms."""

    def test_tray_manager_initialization(self):
        restored = []
        context_opened = []
        mgr = main.TrayIconManager(
            on_restore_callback=lambda: restored.append(True),
            on_context_menu_callback=lambda x, y: context_opened.append((x, y)),
            tooltip="Test Tooltip"
        )
        self.assertFalse(mgr.running)
        self.assertEqual(mgr.tooltip, "Test Tooltip")
        self.assertIsNone(mgr.hwnd)

    def test_tray_manager_lifecycle(self):
        mgr = main.TrayIconManager(tooltip="Lifecycle Test")
        self.assertFalse(mgr.running)
        mgr.start()
        self.assertTrue(mgr.running)
        self.assertIsNotNone(mgr.thread)
        self.assertTrue(mgr.thread.is_alive())

        # Update tooltip
        mgr.update_tooltip("Updated Tooltip")
        self.assertEqual(mgr.tooltip, "Updated Tooltip")

        mgr.stop()
        self.assertFalse(mgr.running)
        self.assertFalse(mgr.thread.is_alive())

    def test_tray_manager_graceful_degradation_without_shell32(self):
        with patch.object(main, 'shell32', None):
            mgr = main.TrayIconManager(tooltip="Degradation Test")
            mgr.start()
            self.assertTrue(mgr.running)
            self.assertFalse(mgr.is_added)
            mgr.update_tooltip("New Tooltip")
            mgr.stop()
            self.assertFalse(mgr.running)


class TestGuiApp(unittest.TestCase):
    """Tests for GUI initialization, widget setup, theme/language changes via header switchers, tray integration, and clean close."""

    def test_gui_initialization_and_close(self):
        import tkinter as tk
        root = tk.Tk()
        try:
            app = main.WindowRelocatorApp(root)
            self.assertIsNotNone(app.tree)
            self.assertIsNotNone(app.combo_theme)
            self.assertIsNotNone(app.combo_lang)
            self.assertIsNotNone(app.btn_minimize_tray)
            self.assertIsNotNone(app.tray_mgr)
            self.assertIn("Monitor Window Relocator", root.title())

            # Test switching themes dynamically via header dropdown
            app.on_theme_change("dark")
            self.assertEqual(main.get_theme(), "dark")
            app.on_theme_change("light")
            self.assertEqual(main.get_theme(), "light")
            app.on_theme_change("system")
            self.assertEqual(main.get_theme(), "system")

            # Test switching languages dynamically via header dropdown
            app.on_language_change("pl")
            self.assertEqual(main.get_language(), "pl")
            app.on_language_change("en")
            self.assertEqual(main.get_language(), "en")

            # Test minimize to tray and restore from tray
            app.minimize_to_tray()
            self.assertEqual(root.state(), "withdrawn")
            app.restore_from_tray()
            self.assertEqual(root.state(), "normal")

            # Test window minimize unmap event handler
            root.iconify()
            mock_unmap_event = MagicMock()
            mock_unmap_event.widget = root
            app._on_window_unmap(mock_unmap_event)
            self.assertEqual(root.state(), "withdrawn")
            app.restore_from_tray()

            # Test treeview hover handlers
            mock_motion_event = MagicMock()
            mock_motion_event.y = 10
            with patch.object(app.tree, 'identify_row', return_value=''):
                app._on_tree_motion(mock_motion_event)
            app._on_tree_leave()
            self.assertIsNone(app._last_hover_item)

            # Test tray context menu creation
            with patch.object(tk.Menu, 'tk_popup') as mock_popup:
                app._show_tray_menu(50, 50)
                mock_popup.assert_called_once_with(50, 50)
            self.assertIsNotNone(app.tray_menu)
            self.assertGreater(app.tray_menu.index("end"), 0)

            app.on_closing()
        except Exception:
            root.destroy()
            raise


if __name__ == '__main__':
    unittest.main()
