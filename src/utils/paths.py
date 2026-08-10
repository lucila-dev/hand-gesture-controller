"""Resolve bundled vs development paths (PyInstaller-safe)."""

from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Read-only app resources (defaults, model)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    """Writable per-user data (settings)."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "GestureControl"
    elif sys.platform == "win32":
        base = Path.home() / "AppData" / "Local" / "GestureControl"
    else:
        base = Path.home() / ".config" / "gesture-control"
    base.mkdir(parents=True, exist_ok=True)
    return base
