"""MediaPipe Tasks hand landmark detection."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.request import urlretrieve

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# Landmark indices (MediaPipe Hands — same as classic Solutions API)
WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
from src.utils.paths import app_root, user_data_dir

DEFAULT_MODEL_PATH = app_root() / "models" / "hand_landmarker.task"

HAND_CONNECTIONS = [
    (conn.start, conn.end)
    for conn in vision.HandLandmarksConnections.HAND_CONNECTIONS
]


@dataclass
class HandResult:
    landmarks: List[Tuple[float, float, float]]  # normalized x, y, z
    handedness: str  # "Left" or "Right"
    score: float


def ensure_model(model_path: Path = DEFAULT_MODEL_PATH) -> Path:
    if model_path.exists() and model_path.stat().st_size > 0:
        return model_path
    fallback = user_data_dir() / "hand_landmarker.task"
    if fallback.exists() and fallback.stat().st_size > 0:
        return fallback
    fallback.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading hand landmarker model to {fallback} …")
    urlretrieve(MODEL_URL, fallback)
    return fallback


class HandDetector:
    def __init__(
        self,
        max_hands: int = 1,
        detection_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
        model_path: Optional[Path] = None,
    ) -> None:
        path = ensure_model(Path(model_path) if model_path else DEFAULT_MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._start_ms = int(time.time() * 1000)
        self._last_ts = -1

    def process(self, frame_bgr: np.ndarray) -> List[HandResult]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(time.time() * 1000) - self._start_ms
        if timestamp_ms <= self._last_ts:
            timestamp_ms = self._last_ts + 1
        self._last_ts = timestamp_ms

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        hands: List[HandResult] = []
        if not result.hand_landmarks:
            return hands

        handedness_list = result.handedness or []
        for i, hand_lms in enumerate(result.hand_landmarks):
            landmarks = [(lm.x, lm.y, lm.z) for lm in hand_lms]
            label = "Right"
            score = 0.0
            if i < len(handedness_list) and handedness_list[i]:
                category = handedness_list[i][0]
                # Frame is mirrored; MediaPipe labels are for the unflipped image,
                # so swap left/right for a natural mirrored feed.
                raw = category.category_name
                label = "Left" if raw == "Right" else "Right"
                score = float(category.score)
            hands.append(HandResult(landmarks=landmarks, handedness=label, score=score))
        return hands

    def draw(self, frame_bgr: np.ndarray, hands: List[HandResult]) -> np.ndarray:
        h, w = frame_bgr.shape[:2]
        if not hands:
            cv2.putText(
                frame_bgr,
                "Hold your hand up to the camera",
                (24, h - 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (220, 230, 225),
                2,
                cv2.LINE_AA,
            )
            return frame_bgr

        for hand in hands:
            pts = [(int(x * w), int(y * h)) for x, y, _ in hand.landmarks]
            for a, b in HAND_CONNECTIONS:
                cv2.line(frame_bgr, pts[a], pts[b], (80, 200, 120), 2, cv2.LINE_AA)
            for i, (px, py) in enumerate(pts):
                color = (40, 180, 255) if i in (THUMB_TIP, INDEX_TIP, MIDDLE_TIP) else (255, 220, 100)
                cv2.circle(frame_bgr, (px, py), 5, color, -1, cv2.LINE_AA)
            label = f"{hand.handedness} hand"
            cv2.putText(
                frame_bgr,
                label,
                (pts[0][0] - 20, max(24, pts[0][1] - 16)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (40, 220, 160),
                2,
                cv2.LINE_AA,
            )
        return frame_bgr

    def close(self) -> None:
        self._landmarker.close()
