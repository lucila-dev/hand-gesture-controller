"""Recognise hand gestures from 21 MediaPipe landmarks."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from src.hand.detector import (
    INDEX_MCP,
    INDEX_PIP,
    INDEX_TIP,
    MIDDLE_MCP,
    MIDDLE_PIP,
    MIDDLE_TIP,
    PINKY_MCP,
    PINKY_PIP,
    PINKY_TIP,
    RING_MCP,
    RING_PIP,
    RING_TIP,
    THUMB_MCP,
    THUMB_TIP,
    WRIST,
    HandResult,
)

Landmark = Tuple[float, float, float]


def _dist(a: Landmark, b: Landmark) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _finger_up(lms: List[Landmark], tip: int, pip: int, mcp: int) -> bool:
    """Finger clearly extended."""
    wrist = lms[WRIST]
    return (
        _dist(lms[tip], wrist) > _dist(lms[pip], wrist) * 1.08
        and _dist(lms[tip], lms[mcp]) > _dist(lms[pip], lms[mcp]) * 0.85
    )


def _thumb_out(lms: List[Landmark], handedness: str) -> bool:
    tip = lms[THUMB_TIP]
    index_mcp = lms[INDEX_MCP]
    if handedness == "Right":
        return tip[0] < index_mcp[0] - 0.06
    return tip[0] > index_mcp[0] + 0.06


class GestureRecognizer:
    def __init__(self, pinch_threshold: float = 0.5) -> None:
        self.pinch_threshold = pinch_threshold

    def set_pinch_threshold(self, value: float) -> None:
        # Slider 0..1 — higher = easier pinch (larger distance still counts)
        v = max(0.0, min(1.0, float(value)))
        self.pinch_threshold = 0.28 + v * 0.32  # ratio 0.28 (strict) .. 0.60 (easy)

    def hand_size(self, hand: HandResult) -> float:
        return _dist(hand.landmarks[WRIST], hand.landmarks[MIDDLE_MCP]) + 1e-6

    def pinch_ratio(self, hand: HandResult) -> float:
        return _dist(hand.landmarks[THUMB_TIP], hand.landmarks[INDEX_TIP]) / self.hand_size(hand)

    def is_pinching(self, hand: HandResult, releasing: bool = False) -> bool:
        ratio = self.pinch_ratio(hand)
        limit = self.pinch_threshold * (1.25 if releasing else 1.0)
        return ratio < limit

    def recognize(self, hand: HandResult) -> Optional[str]:
        if self.is_pinching(hand):
            return "pinch"

        lms = hand.landmarks
        index = _finger_up(lms, INDEX_TIP, INDEX_PIP, INDEX_MCP)
        middle = _finger_up(lms, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
        ring = _finger_up(lms, RING_TIP, RING_PIP, RING_MCP)
        pinky = _finger_up(lms, PINKY_TIP, PINKY_PIP, PINKY_MCP)
        thumb = _thumb_out(lms, hand.handedness)

        # Strict open palm — all 5 fingers must be clearly out
        if thumb and index and middle and ring and pinky:
            return "open_palm"

        if thumb and not index and not middle and not ring and not pinky:
            tip_y, mcp_y = lms[THUMB_TIP][1], lms[THUMB_MCP][1]
            if tip_y < mcp_y - 0.05:
                return "thumb_up"
            if tip_y > mcp_y + 0.05:
                return "thumb_down"

        if index and middle and not ring and not pinky:
            return "two_fingers"

        if index:
            return "point"

        return "hand"

    @staticmethod
    def cursor_landmark(hand: HandResult) -> Tuple[float, float]:
        return hand.landmarks[INDEX_TIP][0], hand.landmarks[INDEX_TIP][1]

    @staticmethod
    def palm_center(hand: HandResult) -> Tuple[float, float]:
        lms = hand.landmarks
        ids = (WRIST, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP)
        return sum(lms[i][0] for i in ids) / len(ids), sum(lms[i][1] for i in ids) / len(ids)
