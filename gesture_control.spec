# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Gesture Control (macOS .app bundle)."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None
project_dir = Path(SPECPATH)

datas = [
    (str(project_dir / "models" / "hand_landmarker.task"), "models"),
    (str(project_dir / "config" / "defaults.json"), "config"),
]

binaries = []
hiddenimports = collect_submodules("mediapipe")

for package in ("mediapipe", "PySide6", "cv2"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

a = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Gesture Control",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Gesture Control",
)

app = BUNDLE(
    coll,
    name="Gesture Control.app",
    icon=None,
    bundle_identifier="com.gesturecontrol.app",
    info_plist={
        "CFBundleName": "Gesture Control",
        "CFBundleDisplayName": "Gesture Control",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSCameraUsageDescription": "Gesture Control uses your camera to track hand gestures.",
        "NSHighResolutionCapable": True,
    },
)
