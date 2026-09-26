# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for Pa-O Typing Tutor."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

# Dynamically load version and metadata from core/version.py
version_info = runpy.run_path("core/version.py")
VERSION = version_info["__version__"]
APP_NAME = version_info["APP_NAME"]
APP_ID = version_info["APP_ID"]
COPYRIGHT = version_info["COPYRIGHT"]

is_mac = sys.platform == "darwin"
is_win = sys.platform.startswith("win")

icon_file = "assets/img/app.icns" if is_mac else "assets/img/app.ico"

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("assets", "assets"),
        ("LICENSE", "."),
    ],
    hiddenimports=[
        "pynput.keyboard._darwin",
        "pynput.keyboard._win32",
        "pynput.keyboard._xorg",
        "pynput.mouse._darwin",
        "pynput.mouse._win32",
        "pynput.mouse._xorg",
        "qtawesome",
        "qtawesome.iconic_font",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

if is_mac:
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=icon_file,
        bundle_identifier=APP_ID,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleIdentifier": APP_ID,
            "CFBundleVersion": VERSION,
            "CFBundleShortVersionString": VERSION,
            "NSHumanReadableCopyright": COPYRIGHT,
            "NSHighResolutionCapable": "True",
            "NSRequiresAquaSystemAppearance": "False",
            "LSMinimumSystemVersion": "11.0",
            "NSInputMonitoringUsageDescription": (
                "Pa-O Typing Tutor uses input monitoring to detect physical keyboard keys "
                "for real-time finger and key guidance."
            ),
        },
    )
