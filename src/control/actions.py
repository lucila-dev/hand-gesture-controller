"""Mouse / keyboard actions — Quartz on macOS, PyAutoGUI elsewhere."""

from __future__ import annotations

import platform
import subprocess
import time
from typing import Callable, Dict, Optional

import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

try:
    from Quartz import (
        CGEventCreateMouseEvent,
        CGEventPost,
        CGEventSetIntegerValueField,
        kCGEventLeftMouseDown,
        kCGEventLeftMouseDragged,
        kCGEventLeftMouseUp,
        kCGEventMouseMoved,
        kCGEventRightMouseDown,
        kCGEventRightMouseUp,
        kCGHIDEventTap,
        kCGMouseButtonLeft,
        kCGMouseButtonRight,
        kCGMouseEventClickState,
    )

    _QUARTZ = True
except Exception:
    _QUARTZ = False


class ActionController:
    def __init__(self) -> None:
        self._system = platform.system()
        self._mouse_held = False
        pos = pyautogui.position()
        self._x, self._y = int(pos.x), int(pos.y)
        self.last_error: str = ""
        self._handlers: Dict[str, Callable[[], None]] = {
            "left_click": self.left_click,
            "right_click": self.right_click,
            "double_click": self.double_click,
            "play_pause": self.play_pause,
            "volume_up": self.volume_up,
            "volume_down": self.volume_down,
            "open_search": self.open_search,
        }

    @staticmethod
    def check_accessibility() -> tuple[bool, str]:
        """Return whether synthetic mouse events actually move the cursor."""
        try:
            p0 = pyautogui.position()
            if _QUARTZ:
                event = CGEventCreateMouseEvent(
                    None, kCGEventMouseMoved, (int(p0.x) + 8, int(p0.y)), kCGMouseButtonLeft
                )
                CGEventPost(kCGHIDEventTap, event)
            else:
                pyautogui.moveTo(p0.x + 8, p0.y, _pause=False)
            time.sleep(0.05)
            p1 = pyautogui.position()
            if abs(p1.x - p0.x) >= 4:
                pyautogui.moveTo(p0.x, p0.y, _pause=False)
                if _QUARTZ:
                    event = CGEventCreateMouseEvent(
                        None, kCGEventMouseMoved, (int(p0.x), int(p0.y)), kCGMouseButtonLeft
                    )
                    CGEventPost(kCGHIDEventTap, event)
                return True, ""
            return False, "Mouse did not move — grant Accessibility to this app or Python"
        except Exception as exc:
            return False, str(exc)

    def perform(self, action: str) -> bool:
        handler = self._handlers.get(action)
        if not handler:
            return False
        try:
            handler()
            if not self.last_error:
                return True
            return False
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def _post(self, event_type, button=kCGMouseButtonLeft, click_state: int = 1) -> None:
        event = CGEventCreateMouseEvent(None, event_type, (self._x, self._y), button)
        if click_state != 1:
            CGEventSetIntegerValueField(event, kCGMouseEventClickState, click_state)
        CGEventPost(kCGHIDEventTap, event)

    def move_cursor(self, x: int, y: int) -> None:
        self._x, self._y = int(x), int(y)
        try:
            if _QUARTZ:
                et = kCGEventLeftMouseDragged if self._mouse_held else kCGEventMouseMoved
                self._post(et)
            else:
                pyautogui.moveTo(self._x, self._y, _pause=False)
            self.last_error = ""
        except Exception as exc:
            self.last_error = f"move: {exc}"

    def mouse_down(self) -> None:
        if self._mouse_held:
            return
        try:
            if _QUARTZ:
                self._post(kCGEventLeftMouseDown)
            else:
                pyautogui.mouseDown(self._x, self._y, button="left", _pause=False)
            self._mouse_held = True
            self.last_error = ""
        except Exception as exc:
            self.last_error = f"down: {exc}"

    def mouse_up(self) -> None:
        if not self._mouse_held:
            return
        try:
            if _QUARTZ:
                self._post(kCGEventLeftMouseUp)
            else:
                pyautogui.mouseUp(button="left", _pause=False)
            self.last_error = ""
        except Exception as exc:
            self.last_error = f"up: {exc}"
        self._mouse_held = False

    def ensure_mouse_up(self) -> None:
        self.mouse_up()

    def left_click(self) -> None:
        self.ensure_mouse_up()
        try:
            if _QUARTZ:
                self._post(kCGEventLeftMouseDown, click_state=1)
                time.sleep(0.02)
                self._post(kCGEventLeftMouseUp, click_state=1)
            else:
                pyautogui.click(self._x, self._y, button="left", _pause=False)
            self.last_error = ""
        except Exception as exc:
            self.last_error = f"click: {exc}"
            try:
                pyautogui.click(self._x, self._y, button="left", _pause=False)
                self.last_error = ""
            except Exception as exc2:
                self.last_error = f"click: {exc2}"

    def right_click(self) -> None:
        self.ensure_mouse_up()
        try:
            if _QUARTZ:
                self._post(kCGEventRightMouseDown, kCGMouseButtonRight)
                self._post(kCGEventRightMouseUp, kCGMouseButtonRight)
            else:
                pyautogui.click(self._x, self._y, button="right", _pause=False)
            self.last_error = ""
        except Exception as exc:
            self.last_error = f"right: {exc}"

    def double_click(self) -> None:
        self.ensure_mouse_up()
        try:
            if _QUARTZ:
                self._post(kCGEventLeftMouseDown, click_state=1)
                self._post(kCGEventLeftMouseUp, click_state=1)
                time.sleep(0.05)
                self._post(kCGEventLeftMouseDown, click_state=2)
                self._post(kCGEventLeftMouseUp, click_state=2)
            else:
                pyautogui.doubleClick(self._x, self._y, _pause=False)
            self.last_error = ""
        except Exception as exc:
            self.last_error = f"dbl: {exc}"

    def scroll(self, dy: int) -> None:
        if not dy:
            return
        try:
            pyautogui.scroll(int(dy))
        except Exception as exc:
            self.last_error = f"scroll: {exc}"

    def zoom(self, steps: int) -> None:
        if not steps:
            return
        try:
            pyautogui.keyDown("ctrl")
            pyautogui.scroll(int(steps))
            pyautogui.keyUp("ctrl")
        except Exception as exc:
            self.last_error = f"zoom: {exc}"
            try:
                pyautogui.keyUp("ctrl")
            except Exception:
                pass

    def play_pause(self) -> None:
        pyautogui.press("playpause")

    def open_search(self) -> None:
        if self._system == "Darwin":
            pyautogui.hotkey("command", "space")
        else:
            pyautogui.press("win")

    def volume_up(self) -> None:
        self._mac_volume_delta(1) if self._system == "Darwin" else pyautogui.press("volumeup")

    def volume_down(self) -> None:
        self._mac_volume_delta(-1) if self._system == "Darwin" else pyautogui.press("volumedown")

    @staticmethod
    def _mac_volume_delta(steps: int) -> None:
        script = f"""
        set cur to output volume of (get volume settings)
        set cur to cur + ({steps} * 6)
        if cur > 100 then set cur to 100
        if cur < 0 then set cur to 0
        set volume output volume cur
        """
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)

    def action_label(self, action: Optional[str]) -> str:
        labels = {
            "left_click": "CLICK",
            "right_click": "Right Click",
            "double_click": "Double Click",
            "drag": "DRAG",
            "zoom": "ZOOM",
            "move_cursor": "MOVE",
            "idle": "FROZEN",
            "pinch": "PINCH",
            "volume_up": "Vol+",
            "volume_down": "Vol-",
            "none": "—",
        }
        return labels.get(action or "", action or "—")
