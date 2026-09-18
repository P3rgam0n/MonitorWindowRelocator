# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-09-18

### Added
- **Seamless Minimize to System Tray**:
  - Added automatic window taskbar suppression upon clicking standard minimize button (`_` / `iconic` state via `<Unmap>`), withdrawing the window completely from the Windows taskbar.
  - Application stays active exclusively in the notification area (System Tray) while minimized.
  - Restoring from system tray via icon click or tray context menu restores the window and reappears on the taskbar seamlessly.

### Changed
- **Modern Neutral Dark UI & Styling Refactoring**:
  - Replaced deep blue/slate tones with modern, sleek Neutral Dark color palette:
    - Main window background: `#121212`
    - Container cards and panels (`TLabelframe`, `Card.TFrame`): `#1e1e1e`
    - Tables and input fields (`Treeview`, `Combobox`): `#181818`
    - Column headers (`Treeview.Heading`): `#232323`
    - Subtle 1px borders: `#2a2a2a` (completely removed bright blue outlines)
    - Primary text: `#e0e0e0`, secondary text: `#9e9e9e`
    - Primary action buttons: modern accent blue `#2563eb` (hover `#1d4ed8`, active `#1e40af`)
    - Standard buttons: clean neutral `#2a2a2a` (hover `#383838`, active `#1f1f1f`)
    - Flat scrollbars: `#3a3a3a` thumb on `#181818` trough without borders
  - Enhanced table row ergonomics: increased row height (`rowheight=28`) and added dynamic row hover highlight (`#252525`).
  - Refactored `TLabelframe` containers into sleek flat cards with subtle 1px `#2a2a2a` borders and neutral `#e0e0e0` titles.

## [1.3.0] - 2026-09-18

### Added
- **System Tray Integration**:
  - Implemented zero-dependency Windows notification area manager (`TrayIconManager`) using pure Win32 API (`Shell_NotifyIconW`, `NOTIFYICONDATAW`, `WNDCLASSEXW`).
  - Added "Minimize to Tray" button to GUI bottom bar allowing users to hide the window from the Windows taskbar.
  - Added context menu on tray icon right-click with theme-matched colors (Show Window, Move Active to Mouse, Gather Hidden Windows, Exit).
  - Added single-click / double-click left mouse button restoration to bring application back to front.
  - Added configurable `minimize_to_tray` option in `config.json` and API getters/setters (`get_minimize_to_tray`, `set_minimize_to_tray`).
  - Added complete Polish (`pl`) and English (`en`) localization for all System Tray elements and actions.
- **Automated Test Suite Expansion**:
  - Expanded test suite to 51 automated unit tests with comprehensive coverage of `TrayIconManager` lifecycle, graceful degradation without shell32, tray context menu callbacks, and config persistence.

### Changed
- **Dark Theme Polish & Background Artifact Elimination**:
  - Upgraded Dark Theme palette to sleek Slate & Sky modern color scheme (`#0f172a`, `#1e293b`, `#334155`, `#38bdf8`, `#f8fafc`).
  - Eliminated contrasting background bounding boxes and label artifact squares inside card containers by properly applying `Card.TLabel` and `Card.TFrame` styles.
  - Unified theme palette styling across treeview headers, scrollbars, comboboxes, and menus.

## [1.2.0] - 2026-09-15

### Added
- **Dark Theme**:
  - Added modern, high-contrast Dark Theme palette tailored for readability in low-light environments.
  - Added dynamic in-app theme switcher supporting `System Default`, `Dark Theme`, and `Light Theme`.
  - Added Windows 10/11 system dark mode auto-detection via Windows Registry (`AppsUseLightTheme`).
  - Implemented Win32 immersive dark title bar via Desktop Window Manager (`DwmSetWindowAttribute`).
  - Added CLI argument `--theme {system,dark,light}`.
- **Application Icon & Visual Assets**:
  - Added multi-resolution Windows application icon (`assets/icon.ico`) with 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, and 256x256 pixel layers.
  - Added high-resolution branding PNG assets in `assets/`.
  - Configured icon for GUI window header, taskbar, and standalone executable binary.
- **Standalone Executable & Automated Release Pipeline**:
  - Added standalone executable build script `build_exe.py` powered by PyInstaller with automatic asset embedding and release ZIP packaging.
  - Configured GitHub Actions workflow (`.github/workflows/build-release.yml`) for automated test execution, binary compilation on `windows-latest`, and GitHub Releases artifact publishing upon version tag push (`v*`).
- **Standard Project Versioning**:
  - Added `VERSION` manifest file adhering to SemVer 2.0.0.
  - Expanded automated unit test suite to 46 tests covering themes, asset resolution, dark title bar integration, and CLI options.

### Changed
- Streamlined UI by centralizing language and theme selection exclusively in top-right header dynamic switchers, removing redundant menu bar.
- Refactored Tkinter widget layout and styles for seamless dark/light mode rendering.
- Enhanced CLI execution mode to attach to parent console seamlessly in standalone binary mode.

## [1.1.0] - 2026-09-10

### Added
- Multi-language support with instant runtime switching between English and Polish.
- Configuration persistence in `config.json`.
- Arbitrary monitor index support (`--mon N`).
- Comprehensive automated test suite (`test_relocator.py`).

## [1.0.0] - 2026-09-01

### Added
- Initial production release of Monitor Window Relocator.
- Win32 API window relocation core for multi-monitor setups.
- Global system hotkeys (`Ctrl+Alt+M`, `Ctrl+Alt+G`, `Ctrl+Alt+1..3`).
- Desktop window enumeration and off-screen detection algorithm.
- GUI interface built with Tkinter.
