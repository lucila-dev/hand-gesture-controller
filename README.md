# Gesture Control

Control your computer with hand gestures via webcam.

**Stack:** Python · OpenCV · MediaPipe · PyAutoGUI · PySide6

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --no-compile -r requirements.txt
```

The hand landmarker model (`models/hand_landmarker.task`) is included. If missing, it downloads automatically on first run.

## Run

```bash
source .venv/bin/activate
python main.py
```

On macOS, grant **Camera** and **Accessibility** permissions when prompted
(System Settings → Privacy & Security) so the app can use the webcam and
control the cursor / keys.

## Gestures

| Gesture | Default action |
| --- | --- |
| Index finger (point) | Move cursor |
| Pinch thumb + index, then open | Left click |
| Hold pinch ~0.3s | Drag / highlight |
| Two fingers, move up/down | Zoom |
| Thumb up / down | Volume up / down |
| Open palm (hold briefly) | Freeze pointer |

Open **Settings** in the app to remap gestures and adjust sensitivity,
smoothing, stability frames, and action cooldown.
