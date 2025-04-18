"""Load and persist application settings."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS_PATH = ROOT / "config" / "defaults.json"
USER_SETTINGS_PATH = ROOT / "config" / "settings.json"

ACTION_CHOICES = [
    ("left_click", "Click / Drag (hold pinch)"),
    ("right_click", "Right Click"),
    ("double_click", "Double Click"),
    ("play_pause", "Play / Pause"),
    ("volume_up", "Volume Up"),
    ("volume_down", "Volume Down"),
    ("open_search", "Open Search (Spotlight)"),
    ("toggle_controls", "Enable / Disable Controls"),
    ("move_cursor", "Move Cursor"),
    ("none", "None"),
]

GESTURE_LABELS = {
    "point": "Index Finger (Point)",
    "pinch": "Pinch",
    "two_fingers": "Two Fingers",
    "thumb_up": "Thumb Up",
    "thumb_down": "Thumb Down",
    "open_palm": "Open Palm",
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def default_settings() -> dict[str, Any]:
    return deepcopy(_load_json(DEFAULTS_PATH))


def load_settings() -> dict[str, Any]:
    settings = default_settings()
    if USER_SETTINGS_PATH.exists():
        user = _load_json(USER_SETTINGS_PATH)
        settings.update({k: v for k, v in user.items() if k != "gesture_actions"})
        if "gesture_actions" in user:
            settings["gesture_actions"].update(user["gesture_actions"])
    return settings


def save_settings(settings: dict[str, Any]) -> None:
    USER_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with USER_SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
