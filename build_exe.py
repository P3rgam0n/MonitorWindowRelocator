"""
Build Script for Monitor Window Relocator
=========================================
Builds a standalone, single-file Windows executable (.exe) using PyInstaller,
bundles multi-resolution icons and application assets, and creates a distribution ZIP archive.

Usage:
    python build_exe.py
"""

import os
import shutil
import subprocess
import sys
import zipfile

APP_NAME = "MonitorWindowRelocator"
MAIN_SCRIPT = "main.py"
ASSETS_DIR = "assets"
ICON_ICO = os.path.join(ASSETS_DIR, "icon.ico")
ICON_PNG = os.path.join(ASSETS_DIR, "icon.png")
DIST_DIR = "dist"
BUILD_DIR = "build"


def get_version():
    """Reads the project version from VERSION file or returns default."""
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "1.3.0"


def ensure_icons():
    """Ensures icon.ico and icon.png exist, generating them from source if necessary."""
    os.makedirs(ASSETS_DIR, exist_ok=True)

    if os.path.exists(ICON_ICO) and os.path.exists(ICON_PNG):
        return

    src_candidates = [
        os.path.join(ASSETS_DIR, "MonitorWindowRelocator_Icon.png"),
        os.path.join(ASSETS_DIR, "icon.png"),
        "MonitorWindowRelocator.png"
    ]
    src_png = None
    for cand in src_candidates:
        if os.path.exists(cand):
            src_png = cand
            break

    if src_png:
        try:
            from PIL import Image
            img = Image.open(src_png)
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(ICON_ICO, format="ICO", sizes=sizes)
            if not os.path.exists(ICON_PNG):
                shutil.copyfile(src_png, ICON_PNG)
            print(f"[Build] Generated '{ICON_ICO}' from '{src_png}'")
        except Exception as e:
            print(f"[Build] Warning: Could not generate .ico: {e}")


def clean_build_artifacts():
    """Cleans previous build artifacts."""
    for folder in [BUILD_DIR, DIST_DIR]:
        if os.path.exists(folder):
            print(f"[Build] Removing old {folder}/ directory...")
            shutil.rmtree(folder, ignore_errors=True)
    spec_file = f"{APP_NAME}.spec"
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
        except Exception:
            pass


def run_pyinstaller():
    """Executes PyInstaller to build a standalone single-file binary."""
    print("[Build] Running PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        f"--add-data={ASSETS_DIR};{ASSETS_DIR}",
    ]

    if os.path.exists(ICON_ICO):
        cmd.append(f"--icon={ICON_ICO}")

    cmd.append(MAIN_SCRIPT)

    print(f"[Build] Command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[Build] ERROR: PyInstaller failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    exe_path = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
    if not os.path.exists(exe_path):
        print(f"[Build] ERROR: Expected executable '{exe_path}' was not found!")
        sys.exit(1)

    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(f"[Build] SUCCESS: Built standalone binary: '{exe_path}' ({size_mb:.2f} MB)")
    return exe_path


def create_release_zip(exe_path):
    """Packages the binary along with readme, license, and helper bat scripts into a zip archive."""
    version = get_version()
    zip_name = f"{APP_NAME}-v{version}-windows-x64.zip"
    zip_path = os.path.join(DIST_DIR, zip_name)

    files_to_pack = [
        (exe_path, f"{APP_NAME}.exe"),
        ("README.md", "README.md"),
        ("LICENSE", "LICENSE"),
        ("Run_App.bat", "Run_App.bat"),
        ("Gather_Offscreen_Windows.bat", "Gather_Offscreen_Windows.bat"),
    ]

    print(f"[Build] Creating release package '{zip_path}'...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arcname in files_to_pack:
            if os.path.exists(src):
                zf.write(src, arcname)
                print(f"  + Added: {arcname}")

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[Build] Release package created: '{zip_path}' ({zip_size_mb:.2f} MB)")
    return zip_path


def main():
    print("=" * 60)
    print(f"  Building {APP_NAME} v{get_version()}")
    print("=" * 60)

    ensure_icons()
    clean_build_artifacts()
    exe_path = run_pyinstaller()
    create_release_zip(exe_path)

    print("=" * 60)
    print("  Build completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
