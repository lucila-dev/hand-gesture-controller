"""Floating on-screen keyboard for gesture (or mouse) typing and search."""

from __future__ import annotations

import time
import urllib.parse
import webbrowser
from typing import Optional

import pyautogui
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


ROWS = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]


class KeyboardWindow(QWidget):
    closed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gesture Keyboard")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumWidth(720)
        self._shifted = False
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        title = QLabel("Search & Type")
        title_font = QFont("Avenir Next", 18)
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setObjectName("kbTitle")
        hint = QLabel("Point at a key and pinch to type · or use your physical keyboard")
        hint.setObjectName("kbHint")
        root.addWidget(title)
        root.addWidget(hint)

        self.field = QLineEdit()
        self.field.setPlaceholderText("Type something to search…")
        self.field.setObjectName("kbField")
        self.field.setMinimumHeight(44)
        self.field.returnPressed.connect(self._search_spotlight)
        root.addWidget(self.field)

        actions = QHBoxLayout()
        self.search_btn = QPushButton("Search Mac")
        self.search_btn.setObjectName("kbPrimary")
        self.search_btn.clicked.connect(self._search_spotlight)
        self.web_btn = QPushButton("Google")
        self.web_btn.setObjectName("kbSecondary")
        self.web_btn.clicked.connect(self._search_google)
        self.type_btn = QPushButton("Type into App")
        self.type_btn.setObjectName("kbSecondary")
        self.type_btn.clicked.connect(self._type_into_app)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("kbSecondary")
        self.clear_btn.clicked.connect(self.field.clear)
        actions.addWidget(self.search_btn)
        actions.addWidget(self.web_btn)
        actions.addWidget(self.type_btn)
        actions.addWidget(self.clear_btn)
        root.addLayout(actions)

        grid = QGridLayout()
        grid.setSpacing(6)
        self._key_buttons: list[QPushButton] = []

        for r, row in enumerate(ROWS):
            offset = 0 if r == 0 else r  # slight stagger
            for c, letter in enumerate(row):
                btn = self._make_key(letter, letter.lower())
                grid.addWidget(btn, r, c + offset)
                self._key_buttons.append(btn)

        root.addLayout(grid)

        bottom = QHBoxLayout()
        shift = QPushButton("⇧ Shift")
        shift.setObjectName("kbWide")
        shift.setCheckable(True)
        shift.toggled.connect(self._toggle_shift)
        space = QPushButton("Space")
        space.setObjectName("kbWide")
        space.clicked.connect(lambda: self._insert(" "))
        back = QPushButton("⌫")
        back.setObjectName("kbWide")
        back.clicked.connect(self._backspace)
        enter = QPushButton("Search ↵")
        enter.setObjectName("kbPrimary")
        enter.clicked.connect(self._search_spotlight)
        bottom.addWidget(shift)
        bottom.addWidget(space, stretch=2)
        bottom.addWidget(back)
        bottom.addWidget(enter)
        root.addLayout(bottom)

        digits = QHBoxLayout()
        for d in "1234567890":
            digits.addWidget(self._make_key(d, d))
        root.addLayout(digits)

    def _make_key(self, label: str, value: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("kbKey")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(42)
        btn.setProperty("key_value", value)
        btn.clicked.connect(lambda _=False, b=btn: self._on_key(b))
        return btn

    def _on_key(self, btn: QPushButton) -> None:
        value = str(btn.property("key_value") or btn.text())
        if value.isalpha():
            ch = value.upper() if self._shifted else value.lower()
        else:
            ch = value
        self._insert(ch)
        if self._shifted:
            self._shifted = False
            self._refresh_labels()

    def _insert(self, text: str) -> None:
        self.field.insert(text)
        self.field.setFocus()

    def _backspace(self) -> None:
        self.field.backspace()
        self.field.setFocus()

    def _toggle_shift(self, on: bool) -> None:
        self._shifted = on
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        for btn in self._key_buttons:
            value = str(btn.property("key_value") or "")
            if len(value) == 1 and value.isalpha():
                btn.setText(value.upper() if self._shifted else value.lower())
    def _query(self) -> str:
        return self.field.text().strip()

    def _search_spotlight(self) -> None:
        query = self._query()
        if not query:
            pyautogui.hotkey("command", "space")
            return
        # Open Spotlight and type the query
        pyautogui.hotkey("command", "space")
        time.sleep(0.35)
        pyautogui.write(query, interval=0.02)
        time.sleep(0.1)
        pyautogui.press("enter")

    def _search_google(self) -> None:
        query = self._query()
        if not query:
            webbrowser.open("https://www.google.com")
            return
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        webbrowser.open(url)

    def _type_into_app(self) -> None:
        query = self.field.text()
        if not query:
            return
        # Give user a beat to focus the target field, then type
        time.sleep(0.4)
        pyautogui.write(query, interval=0.02)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #e8efec;
                color: #1c2b27;
                font-family: "Avenir Next", "Segoe UI", sans-serif;
            }
            #kbTitle { color: #0f3d34; }
            #kbHint { color: #4a635c; font-size: 12px; }
            #kbField {
                background: #ffffff;
                border: 1px solid #9bb5ac;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 16px;
            }
            QPushButton#kbKey, QPushButton#kbWide, QPushButton#kbSecondary {
                background: #ffffff;
                border: 1px solid #9bb5ac;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 8px;
            }
            QPushButton#kbKey:hover, QPushButton#kbWide:hover, QPushButton#kbSecondary:hover {
                background: #f4fffb;
            }
            QPushButton#kbKey:pressed, QPushButton#kbWide:pressed {
                background: #cfe3db;
            }
            QPushButton#kbPrimary {
                background: #1a6b56;
                color: #f4fffb;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 14px;
            }
            QPushButton#kbPrimary:hover { background: #155a48; }
            """
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        self.closed.emit()
        event.accept()

    def focus_field(self) -> None:
        self.field.setFocus()
        self.field.selectAll()
