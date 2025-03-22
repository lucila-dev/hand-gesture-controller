"""Cursor smoothing and screen mapping."""

from __future__ import annotations

from typing import Optional, Tuple

import pyautogui


class CursorSmoother:
    """Exponential moving average for natural cursor motion."""

    def __init__(self, smoothing: float = 0.45) -> None:
        # Higher smoothing = heavier lag / smoother motion (0–1)
        self.smoothing = max(0.0, min(0.95, smoothing))
        self._x: Optional[float] = None
        self._y: Optional[float] = None
        self._screen_w, self._screen_h = pyautogui.size()

    def set_smoothing(self, value: float) -> None:
        self.smoothing = max(0.0, min(0.95, value))

    def refresh_screen_size(self) -> None:
        self._screen_w, self._screen_h = pyautogui.size()

    def reset(self) -> None:
        self._x = None
        self._y = None

    def map_and_smooth(
        self,
        norm_x: float,
        norm_y: float,
        sensitivity: float = 0.6,
    ) -> Tuple[int, int]:
        """
        Map normalized hand coords (0–1) to screen pixels with edge padding
        controlled by sensitivity (higher = use more of the frame / reach edges easier).
        """
        # Active region shrinks when sensitivity is low (harder to reach screen edges)
        pad = 0.25 * (1.0 - max(0.05, min(1.0, sensitivity)))
        x = (norm_x - pad) / max(1e-6, 1.0 - 2 * pad)
        y = (norm_y - pad) / max(1e-6, 1.0 - 2 * pad)
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        target_x = x * (self._screen_w - 1)
        target_y = y * (self._screen_h - 1)

        alpha = 1.0 - self.smoothing
        if self._x is None or self._y is None:
            self._x, self._y = target_x, target_y
        else:
            self._x = self._x * self.smoothing + target_x * alpha
            self._y = self._y * self.smoothing + target_y * alpha

        return int(self._x), int(self._y)
