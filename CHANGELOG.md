# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-15

### Added
- **Dark Theme (Ciemny motyw)**:
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
- Refactored Tkinter widget layout to include top-right Theme and Language controls.
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
