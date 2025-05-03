"""Main application window with live webcam preview."""

from __future__ import annotations

from typing import Any, Dict, Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.engine import GestureEngine
from src.ui.keyboard_window import KeyboardWindow
from src.ui.settings_dialog import SettingsDialog
from src.utils.config import GESTURE_LABELS, save_settings


class MainWindow(QMainWindow):
    settings_changed = Signal(dict)

    def __init__(self, settings: Dict[str, Any]) -> None:
        super().__init__()
        self.settings = settings
        self.engine = GestureEngine(settings)
        self._keyboard: Optional[KeyboardWindow] = None
        self._running = False
        self.setWindowTitle("Gesture Control")
        self.setMinimumSize(880, 640)
        self._build_ui()
        self._apply_styles()

        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS
        self._timer.timeout.connect(self._on_tick)

        self._start_camera()
        QTimer.singleShot(800, self._check_mouse_access)

    def _check_mouse_access(self) -> None:
        ok, err = self.engine.actions.check_accessibility()
        self.engine.mouse_ok = ok
        if not ok:
            QMessageBox.warning(
                self,
                "Accessibility required",
                "Gesture Control cannot move your mouse.\n\n"
                f"{err}\n\n"
                "Enable Accessibility for Cursor (or Python):\n"
                "System Settings → Privacy & Security → Accessibility\n\n"
                "Then restart the app.",
            )
            self.status.showMessage("Enable Accessibility, then restart")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 14)
        layout.setSpacing(12)

        brand = QLabel("Gesture Control")
        brand_font = QFont("Avenir Next", 26)
        brand_font.setWeight(QFont.Weight.DemiBold)
        brand.setFont(brand_font)
        brand.setObjectName("brand")
        subtitle = QLabel("Control your computer with hand gestures")
        subtitle.setObjectName("subtitle")
        layout.addWidget(brand)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.keyboard_btn = QPushButton("⌨ Keyboard")
        self.keyboard_btn.setObjectName("toggleBtn")
        self.keyboard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.keyboard_btn.clicked.connect(self._open_keyboard)

        self.test_btn = QPushButton("Test Click")
        self.test_btn.setObjectName("secondaryBtn")
        self.test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_btn.clicked.connect(self._test_click)

        self.retry_btn = QPushButton("Retry Camera")
        self.retry_btn.setObjectName("secondaryBtn")
        self.retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry_btn.clicked.connect(self._start_camera)
        self.retry_btn.hide()

        self.switch_cam_btn = QPushButton("Next Camera")
        self.switch_cam_btn.setObjectName("secondaryBtn")
        self.switch_cam_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.switch_cam_btn.clicked.connect(self._switch_camera)

        self.toggle_btn = QPushButton("Disable Controls")
        self.toggle_btn.setObjectName("secondaryBtn")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle_controls)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("secondaryBtn")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self._open_settings)

        toolbar.addWidget(self.keyboard_btn)
        toolbar.addWidget(self.test_btn)
        toolbar.addWidget(self.retry_btn)
        toolbar.addWidget(self.switch_cam_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.toggle_btn)
        toolbar.addWidget(self.settings_btn)
        layout.addLayout(toolbar)

        self.video = QLabel()
        self.video.setObjectName("video")
        self.video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video.setMinimumHeight(420)
        self.video.setText("Starting camera…")
        layout.addWidget(self.video, stretch=1)

        info = QHBoxLayout()
        self.gesture_label = QLabel("Gesture: —")
        self.gesture_label.setObjectName("infoChip")
        self.action_label = QLabel("Action: —")
        self.action_label.setObjectName("infoChip")
        self.enabled_label = QLabel("Controls: ON")
        self.enabled_label.setObjectName("statusOn")
        info.addWidget(self.gesture_label)
        info.addWidget(self.action_label)
        info.addStretch(1)
        info.addWidget(self.enabled_label)
        layout.addLayout(info)

        hints = QLabel(
            "1) Point with index to MOVE  ·  2) Pinch thumb+index (yellow bar fills) then OPEN to CLICK  ·  "
            "3) Hold pinch to drag/highlight  ·  4) Open palm = stop  ·  Use Test Click to verify mouse works"
        )
        hints.setObjectName("hints")
        hints.setWordWrap(True)
        layout.addWidget(hints)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eef3f1, stop:0.55 #e7eeea, stop:1 #dce8e3
                );
                color: #1c2b27;
                font-family: "Avenir Next", "Segoe UI", sans-serif;
            }
            #brand { color: #0f3d34; letter-spacing: 0.5px; }
            #subtitle { color: #4a635c; font-size: 13px; }
            #video {
                background: #0f1f1c;
                border: 1px solid #9bb5ac;
                border-radius: 12px;
                color: #9bb5ac;
                font-size: 15px;
            }
            #infoChip, #statusOn, #statusOff {
                background: rgba(255,255,255,0.72);
                border: 1px solid #b7cac3;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            #statusOn { color: #0f6b4c; font-weight: 600; }
            #statusOff { color: #8a3b2a; font-weight: 600; }
            #hints { color: #456059; font-size: 12px; padding: 2px 2px 0; }
            QPushButton#toggleBtn, QPushButton#secondaryBtn {
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#toggleBtn {
                background: #1a6b56;
                color: #f4fffb;
            }
            QPushButton#toggleBtn:hover { background: #155a48; }
            QPushButton#secondaryBtn {
                background: #ffffff;
                color: #1a3c34;
                border: 1px solid #9bb5ac;
            }
            QPushButton#secondaryBtn:hover { background: #f7fbf9; }
            QStatusBar {
                background: transparent;
                color: #4a635c;
            }
            """
        )

    def _start_camera(self) -> None:
        self._timer.stop()
        self.video.setText("Starting camera…")
        self.retry_btn.hide()
        if not self.engine.start():
            self._running = False
            self.video.setText(
                "Camera unavailable\n\n"
                "macOS blocked webcam access.\n"
                "System Settings → Privacy & Security → Camera\n"
                "Enable Cursor (or Terminal), then click Retry Camera."
            )
            self.retry_btn.show()
            self.status.showMessage("Camera permission required")
            QMessageBox.warning(
                self,
                "Camera permission needed",
                "Allow Camera access for Cursor (or the app that launched this),\n"
                "then click Retry Camera.\n\n"
                "System Settings → Privacy & Security → Camera",
            )
            return
        save_settings(self.settings)
        self.retry_btn.hide()
        self._running = True
        self._timer.start()
        cams = self.engine.available_cameras or [self.engine.camera.camera_index]
        self.status.showMessage(
            f"Camera {self.engine.camera.camera_index} connected "
            f"({len(cams)} available) — hold your hand in view"
        )

    def _switch_camera(self) -> None:
        if not self._running:
            return
        self._timer.stop()
        if not self.engine.switch_camera():
            self.status.showMessage("No other camera found")
            self._timer.start()
            return
        save_settings(self.settings)
        self._timer.start()
        self.status.showMessage(
            f"Switched to camera {self.engine.camera.camera_index} — "
            "use FaceTime camera if you see ceiling/phone view"
        )

    def _on_tick(self) -> None:
        if not self._running:
            return
        # Keep running even if another window is focused — only stop when closed/hidden
        if self.isMinimized():
            return

        frame, state = self.engine.process_frame()
        if frame is not None:
            self._show_frame(frame)

        gesture_text = GESTURE_LABELS.get(state.gesture or "", state.gesture or "—")
        self.gesture_label.setText(f"Gesture: {gesture_text}")
        action_text = self.engine.actions.action_label(state.action) if state.action else "—"
        self.action_label.setText(f"Action: {action_text}")
        self._update_enabled_ui(state.controls_enabled)
        self.status.showMessage(state.status_message)

    def _show_frame(self, frame_bgr: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        pix = QPixmap.fromImage(image)
        self.video.setPixmap(
            pix.scaled(
                self.video.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _update_enabled_ui(self, enabled: bool) -> None:
        if enabled:
            self.enabled_label.setText("Controls: ON")
            self.enabled_label.setObjectName("statusOn")
            self.toggle_btn.setText("Disable Controls")
        else:
            self.enabled_label.setText("Controls: OFF")
            self.enabled_label.setObjectName("statusOff")
            self.toggle_btn.setText("Enable Controls")
        self.enabled_label.style().unpolish(self.enabled_label)
        self.enabled_label.style().polish(self.enabled_label)

    def _toggle_controls(self) -> None:
        self.engine.controls_enabled = not self.engine.controls_enabled
        self.settings["controls_enabled"] = self.engine.controls_enabled
        save_settings(self.settings)
        self._update_enabled_ui(self.engine.controls_enabled)

    def _test_click(self) -> None:
        """Verify OS mouse control without gestures."""
        import pyautogui

        self.status.showMessage("Testing mouse in 1 second — watch the cursor…")
        QApplication.processEvents()
        pos = pyautogui.position()
        self.engine.actions.move_cursor(pos.x, pos.y)
        QTimer.singleShot(400, lambda: self._run_test_click(pos.x, pos.y))

    def _run_test_click(self, x: int, y: int) -> None:
        self.engine.actions.move_cursor(x, y)
        self.engine.actions.left_click()
        err = self.engine.actions.last_error
        if err:
            self.status.showMessage(f"Test click FAILED: {err}")
            QMessageBox.warning(
                self,
                "Mouse test failed",
                f"Could not click.\n\n{err}\n\n"
                "On macOS grant Accessibility to Cursor (or Terminal):\n"
                "System Settings → Privacy & Security → Accessibility",
            )
        else:
            self.status.showMessage(f"Test click OK at {x},{y} — if nothing happened, enable Accessibility for Cursor")
            QMessageBox.information(
                self,
                "Mouse test",
                f"Sent a click at ({x}, {y}).\n\n"
                "If you did not see a click on the item under the cursor,\n"
                "enable Accessibility for Cursor:\n"
                "System Settings → Privacy & Security → Accessibility",
            )

    def _open_keyboard(self) -> None:
        if self._keyboard is not None and self._keyboard.isVisible():
            self._keyboard.raise_()
            self._keyboard.focus_field()
            return
        self._keyboard = KeyboardWindow()
        self._keyboard.closed.connect(self._on_keyboard_closed)
        self._keyboard.show()
        self._keyboard.focus_field()
        self.status.showMessage("Keyboard open — type here, then Search Mac / Google")

    def _on_keyboard_closed(self) -> None:
        self._keyboard = None

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.result_settings()
            self.engine.apply_settings(self.settings)
            save_settings(self.settings)
            self.settings_changed.emit(self.settings)
            self.status.showMessage("Settings saved")

    def _shutdown(self) -> None:
        """Stop camera, gestures, and timers — safe to call more than once."""
        self._running = False
        self._timer.stop()
        if self._keyboard is not None:
            self._keyboard.close()
            self._keyboard = None
        try:
            self.engine.actions.ensure_mouse_up()
        except Exception:
            pass
        try:
            self.engine.stop()
        except Exception:
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        self.settings["controls_enabled"] = self.engine.controls_enabled
        save_settings(self.settings)
        self._shutdown()
        event.accept()
        # Fully quit so nothing keeps running after the window closes
        QApplication.instance().quit()

    def hideEvent(self, event) -> None:  # noqa: N802
        # Minimized / hidden → pause camera + gestures
        if self._running:
            self._timer.stop()
            self.engine.camera.release()
            try:
                self.engine.actions.ensure_mouse_up()
            except Exception:
                pass
            self.video.setText("Paused — app hidden")
            self.status.showMessage("Camera and gestures paused while the window is hidden")
        super().hideEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self._running and not self._timer.isActive():
            if self.engine.camera.open():
                self._timer.start()
                self.status.showMessage("Camera and gestures resumed")
