#!/usr/bin/env python3
"""Gesture Control — launch the desktop application."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as `python main.py` from the project root
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from src.ui import MainWindow
from src.utils.config import load_settings


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gesture Control")
    app.setOrganizationName("GestureControl")
    app.setQuitOnLastWindowClosed(True)

    settings = load_settings()
    window = MainWindow(settings)
    window.show()
    code = app.exec()
    # Belt-and-suspenders: if anything is still holding the camera, release it
    try:
        window._shutdown()
    except Exception:
        pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
