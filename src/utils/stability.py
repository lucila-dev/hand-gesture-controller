"""Gesture stability filter and action cooldowns."""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional


class GestureStabilizer:
    """Require the same gesture for N consecutive frames before accepting it."""

    def __init__(self, required_frames: int = 6) -> None:
        self.required_frames = max(1, required_frames)
        self._history: Deque[Optional[str]] = deque(maxlen=self.required_frames)
        self._stable: Optional[str] = None

    def update_required_frames(self, frames: int) -> None:
        frames = max(1, frames)
        if frames == self.required_frames:
            return
        self.required_frames = frames
        self._history = deque(self._history, maxlen=frames)

    def update(self, gesture: Optional[str]) -> Optional[str]:
        self._history.append(gesture)
        if len(self._history) < self.required_frames:
            return self._stable
        if all(g == gesture for g in self._history):
            self._stable = gesture
        return self._stable

    def reset(self) -> None:
        self._history.clear()
        self._stable = None


class CooldownTracker:
    """Prevent rapid re-firing of discrete gesture actions."""

    def __init__(self, cooldown_ms: int = 800) -> None:
        self.cooldown_ms = max(0, cooldown_ms)
        self._last_fire: dict[str, float] = {}

    def update_cooldown(self, cooldown_ms: int) -> None:
        self.cooldown_ms = max(0, cooldown_ms)

    def ready(self, key: str) -> bool:
        last = self._last_fire.get(key)
        if last is None:
            return True
        return (time.monotonic() - last) * 1000 >= self.cooldown_ms

    def mark(self, key: str) -> None:
        self._last_fire[key] = time.monotonic()

    def clear(self) -> None:
        self._last_fire.clear()
