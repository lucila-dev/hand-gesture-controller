"""OpenCV webcam capture."""

from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np


def list_cameras(max_index: int = 6) -> List[int]:
    """Return camera indexes that open and return at least one frame."""
    found: List[int] = []
    backend = cv2.CAP_AVFOUNDATION if hasattr(cv2, "CAP_AVFOUNDATION") else cv2.CAP_ANY
    for index in range(max_index):
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue
        ok, frame = cap.read()
        cap.release()
        if ok and frame is not None:
            found.append(index)
    return found


class CameraCapture:
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480) -> None:
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._cap: Optional[cv2.VideoCapture] = None

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def open(self) -> bool:
        self.release()
        backends = []
        if hasattr(cv2, "CAP_AVFOUNDATION"):
            backends.append(cv2.CAP_AVFOUNDATION)
        backends.append(cv2.CAP_ANY)

        for backend in backends:
            self._cap = cv2.VideoCapture(self.camera_index, backend)
            if self._cap is not None and self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self._cap.set(cv2.CAP_PROP_FPS, 30)
                ok, _ = self._cap.read()
                if ok:
                    return True
                self.release()
            else:
                self.release()
        return False

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_open:
            return False, None
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return False, None
        frame = cv2.flip(frame, 1)
        return True, frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
