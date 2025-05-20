"""Settings dialog for gesture mappings and sensitivity."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.utils.config import ACTION_CHOICES, GESTURE_LABELS


class SettingsDialog(QDialog):
    settings_applied = Signal(dict)

    def __init__(self, settings: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gesture Control — Settings")
        self.setMinimumWidth(420)
        self._settings = deepcopy(settings)
        self._gesture_combos: Dict[str, QComboBox] = {}

        root = QVBoxLayout(self)
        root.setSpacing(16)

        mapping_box = QGroupBox("Gesture → Action")
        form = QFormLayout(mapping_box)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setSpacing(10)

        actions = self._settings.setdefault("gesture_actions", {})
        for key, label in GESTURE_LABELS.items():
            combo = QComboBox()
            for value, text in ACTION_CHOICES:
                combo.addItem(text, value)
            current = actions.get(key, "none")
            idx = combo.findData(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            # Point should prefer move_cursor; open_palm prefers toggle
            self._gesture_combos[key] = combo
            form.addRow(QLabel(label), combo)

        root.addWidget(mapping_box)

        sens_box = QGroupBox("Sensitivity & Timing")
        sens_form = QFormLayout(sens_box)

        self.sensitivity = self._make_slider(5, 100, int(self._settings.get("sensitivity", 0.6) * 100))
        self.smoothing = self._make_slider(0, 90, int(self._settings.get("cursor_smoothing", 0.45) * 100))
        self.stability = self._make_slider(2, 15, int(self._settings.get("stability_frames", 6)))
        self.cooldown = self._make_slider(200, 2000, int(self._settings.get("action_cooldown_ms", 800)))
        self.pinch = self._make_slider(2, 12, int(self._settings.get("pinch_threshold", 0.05) * 100))

        sens_form.addRow(self._slider_row("Cursor reach", self.sensitivity, self._pct))
        sens_form.addRow(self._slider_row("Cursor smoothing", self.smoothing, self._pct))
        sens_form.addRow(self._slider_row("Stability (frames)", self.stability, str))
        sens_form.addRow(self._slider_row("Action cooldown (ms)", self.cooldown, str))
        sens_form.addRow(self._slider_row("Pinch distance", self.pinch, self._pct))
        root.addWidget(sens_box)

        self.show_landmarks = QCheckBox("Show hand landmarks on video")
        self.show_landmarks.setChecked(bool(self._settings.get("show_landmarks", True)))
        root.addWidget(self.show_landmarks)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background: #f3f5f4; }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #cfd8d4;
                border-radius: 8px;
                margin-top: 10px;
                padding: 12px 10px 8px;
                background: #fafcfb;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #1a3c34;
            }
            QLabel { color: #24312e; }
            QComboBox, QSlider { min-height: 24px; }
            """
        )

    @staticmethod
    def _make_slider(mn: int, mx: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(mn, mx)
        slider.setValue(value)
        return slider

    @staticmethod
    def _pct(v: int) -> str:
        return f"{v}%"

    def _slider_row(self, title: str, slider: QSlider, fmt) -> QWidget:
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setMinimumWidth(150)
        value_label = QLabel(fmt(slider.value()))
        value_label.setMinimumWidth(48)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        slider.valueChanged.connect(lambda v, lab=value_label, f=fmt: lab.setText(f(v)))
        layout.addWidget(label)
        layout.addWidget(slider, stretch=1)
        layout.addWidget(value_label)
        return wrap

    def _accept(self) -> None:
        gesture_actions = {}
        for key, combo in self._gesture_combos.items():
            gesture_actions[key] = combo.currentData()
        self._settings["gesture_actions"] = gesture_actions
        self._settings["sensitivity"] = self.sensitivity.value() / 100.0
        self._settings["cursor_smoothing"] = self.smoothing.value() / 100.0
        self._settings["stability_frames"] = self.stability.value()
        self._settings["action_cooldown_ms"] = self.cooldown.value()
        self._settings["pinch_threshold"] = self.pinch.value() / 100.0
        self._settings["show_landmarks"] = self.show_landmarks.isChecked()
        self.settings_applied.emit(self._settings)
        self.accept()

    def result_settings(self) -> Dict[str, Any]:
        return self._settings
