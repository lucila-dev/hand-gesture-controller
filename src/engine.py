"""Simple gesture → action pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from src.camera import CameraCapture
from src.camera.capture import list_cameras
from src.control import ActionController, CursorSmoother
from src.hand import GestureRecognizer, HandDetector
from src.utils.stability import CooldownTracker


@dataclass
class FrameState:
    gesture: Optional[str] = None
    raw_gesture: Optional[str] = None
    action: Optional[str] = None
    controls_enabled: bool = True
    hand_detected: bool = False
    status_message: str = "No hand detected"
    cursor_xy: Optional[Tuple[int, int]] = None
    camera_index: int = 0
    just_clicked: bool = False
    pinch_ratio: float = 0.0


class GestureEngine:
    def __init__(self, settings: Dict[str, Any]) -> None:
        self.settings = settings
        self.camera = CameraCapture(camera_index=int(settings.get("camera_index", 0)))
        self.detector = HandDetector(detection_confidence=0.5, tracking_confidence=0.5)
        self.recognizer = GestureRecognizer()
        self.recognizer.set_pinch_threshold(float(settings.get("pinch_threshold", 0.5)))
        self.cooldowns = CooldownTracker(cooldown_ms=300)
        self.smoother = CursorSmoother(smoothing=float(settings.get("cursor_smoothing", 0.2)))
        self.actions = ActionController()
        self.controls_enabled = bool(settings.get("controls_enabled", True))
        self.available_cameras: List[int] = []
        self.state = FrameState(controls_enabled=self.controls_enabled)
        self.mouse_ok = True

        self._pinching = False
        self._pinch_t0 = 0.0
        self._dragging = False
        self._release_frames = 0
        self._zoom_y: Optional[float] = None
        self._zoom_acc = 0.0
        self._palm_frames = 0

    def start(self) -> bool:
        self.available_cameras = list_cameras() or [0]
        if self.camera.camera_index not in self.available_cameras:
            self.camera.camera_index = self.available_cameras[0]
            self.settings["camera_index"] = self.camera.camera_index
        self.smoother.refresh_screen_size()
        ok, err = self.actions.check_accessibility()
        self.mouse_ok = ok
        if not ok:
            self.state.status_message = err
        return self.camera.open()

    def switch_camera(self) -> bool:
        self.available_cameras = list_cameras() or [0]
        if not self.available_cameras:
            return False
        i = (
            self.available_cameras.index(self.camera.camera_index)
            if self.camera.camera_index in self.available_cameras
            else -1
        )
        self.camera.camera_index = self.available_cameras[(i + 1) % len(self.available_cameras)]
        self.settings["camera_index"] = self.camera.camera_index
        self._reset_pinch()
        self.smoother.reset()
        return self.camera.open()

    def stop(self) -> None:
        self._reset_pinch()
        self.camera.release()
        self.detector.close()

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        self.settings = settings
        self.recognizer.set_pinch_threshold(float(settings.get("pinch_threshold", 0.5)))
        self.smoother.set_smoothing(float(settings.get("cursor_smoothing", 0.2)))
        self.controls_enabled = bool(settings.get("controls_enabled", True))

    def _cursor(self, hand, sensitivity: float) -> Tuple[int, int]:
        nx, ny = self.recognizer.cursor_landmark(hand)
        return self.smoother.map_and_smooth(nx, ny, sensitivity=sensitivity)

    def _reset_pinch(self) -> None:
        if self._dragging:
            self.actions.mouse_up()
        self._pinching = False
        self._dragging = False
        self._release_frames = 0

    def _finish_pinch(self) -> Tuple[Optional[str], bool]:
        if not self._pinching:
            return None, False
        held = time.monotonic() - self._pinch_t0
        was_dragging = self._dragging
        self._reset_pinch()

        if was_dragging:
            self.actions.mouse_up()
            return "drag", False

        if held < 1.2 and self.cooldowns.ready("click"):
            self.actions.left_click()
            self.cooldowns.mark("click")
            return "left_click", True
        return None, False

    def process_frame(self) -> Tuple[Optional[np.ndarray], FrameState]:
        ok, frame = self.camera.read()
        if not ok or frame is None:
            self._reset_pinch()
            return None, FrameState(
                controls_enabled=self.controls_enabled,
                status_message="Camera unavailable",
                camera_index=self.camera.camera_index,
            )

        hands = self.detector.process(frame)
        if self.settings.get("show_landmarks", True):
            frame = self.detector.draw(frame, hands)

        sensitivity = float(self.settings.get("sensitivity", 0.85))

        if not hands:
            self._reset_pinch()
            self.smoother.reset()
            self._zoom_y = None
            self._palm_frames = 0
            msg = "Show your hand"
            self._hud(frame, msg, (180, 180, 180))
            return frame, FrameState(
                controls_enabled=self.controls_enabled,
                status_message=msg,
                camera_index=self.camera.camera_index,
            )

        hand = hands[0]
        ratio = self.recognizer.pinch_ratio(hand)
        gesture = self.recognizer.recognize(hand)
        pinching = self.recognizer.is_pinching(hand)
        if self._pinching and not pinching:
            pinching = self.recognizer.is_pinching(hand, releasing=True)

        action: Optional[str] = None
        clicked = False
        xy: Optional[Tuple[int, int]] = None
        self._pinch_hud(frame, hand, ratio, pinching)

        if not self.controls_enabled:
            self._reset_pinch()
            msg = "Controls OFF — click Enable Controls"
            self._hud(frame, msg, (80, 80, 255))
            return frame, FrameState(
                gesture=gesture,
                controls_enabled=False,
                hand_detected=True,
                status_message=msg,
                pinch_ratio=ratio,
                camera_index=self.camera.camera_index,
            )

        if not self.mouse_ok:
            msg = "Enable Accessibility for this app — System Settings → Privacy"
            self._hud(frame, msg, (80, 80, 255))
            return frame, FrameState(
                gesture=gesture,
                controls_enabled=True,
                hand_detected=True,
                status_message=msg,
                pinch_ratio=ratio,
                camera_index=self.camera.camera_index,
            )

        # Open palm — must hold ~8 frames (~250ms) before freezing
        if gesture == "open_palm":
            self._palm_frames += 1
            if self._palm_frames >= 8:
                self._reset_pinch()
                self.smoother.reset()
                self._zoom_y = None
                msg = "OPEN PALM — pointer frozen"
                self._hud(frame, msg, (255, 180, 80))
                return frame, FrameState(
                    gesture="open_palm",
                    action="idle",
                    controls_enabled=True,
                    hand_detected=True,
                    status_message=msg,
                    pinch_ratio=ratio,
                    camera_index=self.camera.camera_index,
                )
        else:
            self._palm_frames = 0

        # --- PINCH (ratio-based, not gesture string) ---
        if pinching:
            xy = self._cursor(hand, sensitivity)
            self.actions.move_cursor(*xy)
            if not self._pinching:
                self._pinching = True
                self._pinch_t0 = time.monotonic()
                self._dragging = False
                self._release_frames = 0
                msg = "PINCH — open fingers to CLICK"
            else:
                self._release_frames = 0
                if not self._dragging and time.monotonic() - self._pinch_t0 > 0.3:
                    self.actions.mouse_down()
                    self._dragging = True
                action = "drag" if self._dragging else "pinch"
                msg = "DRAGGING — open to release" if self._dragging else "PINCH — open to CLICK"
            self._hud(frame, msg, (0, 220, 255))
            return frame, FrameState(
                gesture="pinch",
                action=action,
                controls_enabled=True,
                hand_detected=True,
                status_message=msg,
                cursor_xy=xy,
                pinch_ratio=ratio,
                camera_index=self.camera.camera_index,
            )

        # Pinch released
        if self._pinching:
            self._release_frames += 1
            if self._release_frames >= 1:
                action, clicked = self._finish_pinch()
                err = self.actions.last_error
                if clicked:
                    msg = "CLICKED ✓" if not err else f"Click failed: {err}"
                elif action == "drag":
                    msg = "Drag done"
                else:
                    msg = "Pinch released"
                self._hud(frame, msg, (80, 255, 120) if clicked else (200, 200, 200))
                return frame, FrameState(
                    gesture="pinch",
                    action=action,
                    controls_enabled=True,
                    hand_detected=True,
                    status_message=msg,
                    just_clicked=clicked,
                    pinch_ratio=ratio,
                    camera_index=self.camera.camera_index,
                )
            self._hud(frame, "Releasing…", (0, 220, 255))
            return frame, FrameState(
                gesture="pinch",
                controls_enabled=True,
                hand_detected=True,
                status_message="Releasing…",
                pinch_ratio=ratio,
                camera_index=self.camera.camera_index,
            )

        # --- TWO FINGERS: zoom ---
        if gesture == "two_fingers":
            self.smoother.reset()
            _, py = self.recognizer.palm_center(hand)
            if self._zoom_y is None:
                self._zoom_y = py
                msg = "Move hand UP/DOWN to zoom"
            else:
                self._zoom_acc += (self._zoom_y - py) * 120
                self._zoom_y = py
                step = int(self._zoom_acc)
                if step:
                    self.actions.zoom(step)
                    self._zoom_acc -= step
                    action = "zoom"
                    msg = "ZOOM IN" if step > 0 else "ZOOM OUT"
                else:
                    msg = "Move hand UP/DOWN to zoom"
            self._hud(frame, msg, (255, 200, 80))
            return frame, FrameState(
                gesture="two_fingers",
                action=action,
                controls_enabled=True,
                hand_detected=True,
                status_message=msg,
                pinch_ratio=ratio,
                camera_index=self.camera.camera_index,
            )

        self._zoom_y = None

        # --- DEFAULT: move cursor to index finger ---
        xy = self._cursor(hand, sensitivity)
        self.actions.move_cursor(*xy)
        action = "move_cursor"
        err = self.actions.last_error
        msg = f"MOVE {xy[0]},{xy[1]}"
        if err:
            msg = f"Blocked: {err}"

        if gesture in ("thumb_up", "thumb_down") and self.cooldowns.ready(gesture):
            key = "volume_up" if gesture == "thumb_up" else "volume_down"
            if self.actions.perform(key):
                self.cooldowns.mark(gesture)
                action = key
                msg = "Volume +"

        self._hud(frame, msg, (80, 255, 160) if not err else (80, 80, 255))
        return frame, FrameState(
            gesture=gesture,
            action=action,
            controls_enabled=True,
            hand_detected=True,
            status_message=msg,
            cursor_xy=xy,
            pinch_ratio=ratio,
            camera_index=self.camera.camera_index,
            just_clicked=clicked,
        )

    def _pinch_hud(self, frame, hand, ratio: float, active: bool) -> None:
        h, w = frame.shape[:2]
        t, i = hand.landmarks[4], hand.landmarks[8]
        p1 = (int(t[0] * w), int(t[1] * h))
        p2 = (int(i[0] * w), int(i[1] * h))
        thr = self.recognizer.pinch_threshold
        col = (0, 255, 255) if active else (100, 100, 100)
        cv2.line(frame, p1, p2, col, 4)
        cv2.circle(frame, p1, 10, col, -1)
        cv2.circle(frame, p2, 10, col, -1)
        status = "PINCHING" if active else "open"
        cv2.putText(
            frame,
            f"pinch {ratio:.2f} need < {thr:.2f} ({status})",
            (14, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            col,
            2,
        )

    @staticmethod
    def _hud(frame: np.ndarray, text: str, color: Tuple[int, int, int]) -> None:
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, h - 44), (w, h), (15, 15, 15), -1)
        cv2.putText(
            frame,
            text[:60],
            (10, h - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2,
        )
