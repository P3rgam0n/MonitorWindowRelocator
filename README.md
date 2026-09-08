# 🖥️ Monitor Window Relocator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey.svg)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Languages](https://img.shields.io/badge/languages-English%20%7C%20Polski-green.svg)](#-language-support--wsparcie-językowe)

**Monitor Window Relocator** is a lightweight, zero-dependency Windows utility that solves the common multi-monitor problem where application windows open off-screen on powered-off, sleeping, or disconnected monitors (e.g., in 3-monitor setups).

It allows you to instantly pull any hidden or stranded window back to your active display using global hotkeys, a graphical user interface (GUI), or command-line execution scripts.

---

## 🚀 Key Features

- **Instant Off-Screen Window Recovery**: Automatically scan all running windows and relocate any hidden/stranded windows to your primary monitor.
- **Move to Mouse Cursor**: Bring the active application window straight to whichever monitor your mouse cursor is currently resting on.
- **Direct Monitor Selection**: Move windows directly to Monitor 1, 2, or 3 using single key shortcuts.
- **Global Hotkeys**: Control window positions anytime in the background without focusing the application.
- **Multilingual Support**: Fully localized in **English** (default) and **Polish** with dynamic in-app language switching.
- **Zero External Dependencies**: Built strictly using the Python Standard Library (`ctypes`, `tkinter`). No `pip install` required!
- **High-DPI Aware**: Fully compatible with Windows 10/11 per-monitor DPI scaling setups.

---

## ⌨️ Global Hotkeys

The application runs in the background and responds to system-wide hotkeys:

| Hotkey | Action |
| :--- | :--- |
| **`Ctrl + Alt + M`** | **Move active window** to the monitor under the mouse cursor. |
| **`Ctrl + Alt + G`** | **Gather all hidden / off-screen windows** back to the Primary Monitor. |
| **`Ctrl + Alt + 1`** | Move active window to **Monitor 1**. |
| **`Ctrl + Alt + 2`** | Move active window to **Monitor 2**. |
| **`Ctrl + Alt + 3`** | Move active window to **Monitor 3**. |

---

## 🛠️ Usage & Execution

### Prerequisites
- Operating System: **Windows 10 / 11**
- Python Environment: **Python 3.8+** (included standard Tkinter module)

---

### 1. Running the GUI Application
Launch the graphical interface with full display status and open applications list:

- Double-click `Run_App.bat`
- Or execute via terminal:
  ```cmd
  python main.py
  ```

---

### 2. Standalone Quick Gather (No GUI)
Gather off-screen windows instantly via command line or background script:

- Double-click `Gather_Offscreen_Windows.bat`
- Or execute via terminal:
  ```cmd
  python main.py --gather
  ```

---

### 3. Command Line Arguments

| Argument | Description |
| :--- | :--- |
| `--gather` | Scans and moves all off-screen windows to the primary display and exits. |
| `--to-cursor` | Moves the currently active foreground window to the mouse display and exits. |
| `--mon <1\|2\|3>` | Moves the active foreground window to Monitor 1, 2, or 3 and exits. |
| `--lang <en\|pl>` | Forces startup in the specified language (`en` for English, `pl` for Polish). |
| `--version`, `-v` | Displays version information. |
| `--help`, `-h` | Displays help message and exits. |

---

## 🧪 Testing & Verification

Run the built-in automated test suite with Python's standard unittest runner:
```cmd
python -m unittest test_relocator.py -v
```

---

## 🌐 Language Support / Wsparcie Językowe

The interface automatically detects your Windows system display language (**English** or **Polish**), and can also be switched dynamically at any time:
1. Use the **Language dropdown** in the top-right corner of the window.
2. Or choose `Language -> Polski / English` from the top menu bar.
3. Your preference is automatically saved to `config.json` for future launches.

---

## 📁 Repository Structure

```
MonitorWindowRelocator/
├── main.py                      # Complete application (Core, Win32 API, Hotkeys, i18n, GUI & CLI)
├── test_relocator.py            # Automated unit & integration test suite (34 tests)
├── Run_App.bat                  # Background launcher script for GUI
├── Gather_Offscreen_Windows.bat # Instant CLI script to gather hidden windows
├── LICENSE                      # MIT Open Source License
├── .gitignore                   # Standard Git ignore rules
└── README.md                    # Project documentation
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
