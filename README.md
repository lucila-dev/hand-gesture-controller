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

## Deploy / distribute (macOS)

### Build locally

```bash
chmod +x build-macos.sh
./build-macos.sh
```

Output:
- `dist/Gesture Control.app` — double-click to run
- `dist/Gesture-Control-macOS.zip` — share or upload

On first launch, macOS will ask for **Camera** and **Accessibility** permissions.

### Publish a GitHub Release

Push a version tag — GitHub Actions builds the `.app` and attaches the zip:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Or run **Actions → Release → Run workflow** manually from the repo.

### Notes for public distribution

- Unsigned builds show “unidentified developer” — right-click → Open the first time.
- For wider distribution, sign and notarize with an Apple Developer ID.
- User settings are stored in `~/Library/Application Support/GestureControl/settings.json`.
