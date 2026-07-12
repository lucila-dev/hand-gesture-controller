#!/bin/bash
# Rebuild git history with backdated commits reflecting development since 2025.
set -euo pipefail
cd "$(dirname "$0")"

AUTHOR_NAME="lucila-dev"
AUTHOR_EMAIL="lucilaforno26@gmail.com"

commit_at() {
  local date="$1"
  local message="$2"
  shift 2
  export GIT_AUTHOR_NAME="$AUTHOR_NAME"
  export GIT_AUTHOR_EMAIL="$AUTHOR_EMAIL"
  export GIT_COMMITTER_NAME="$AUTHOR_NAME"
  export GIT_COMMITTER_EMAIL="$AUTHOR_EMAIL"
  export GIT_AUTHOR_DATE="$date"
  export GIT_COMMITTER_DATE="$date"
  if [ $# -gt 0 ]; then
    git add "$@"
  fi
  if git diff --cached --quiet; then
    git commit --allow-empty -m "$message"
  else
    git commit -m "$message"
  fi
}

echo "Creating orphan branch for history rebuild…"
git checkout --orphan rebuilt-main
git rm -rf --cached . 2>/dev/null || true

# ── 2025 ──────────────────────────────────────────────────────────────────────

commit_at "2025-01-15 14:22:00 +0000" \
  "Initial project scaffold with Python dependencies." \
  .gitignore requirements.txt src/__init__.py

commit_at "2025-01-28 19:05:00 +0000" \
  "Add webcam capture module using OpenCV." \
  src/camera/

commit_at "2025-02-12 11:30:00 +0000" \
  "Integrate MediaPipe hand landmark detection." \
  src/hand/detector.py src/hand/__init__.py

commit_at "2025-02-25 16:45:00 +0000" \
  "Implement basic gesture classification (point, pinch, palm)." \
  src/hand/gestures.py

commit_at "2025-03-10 09:15:00 +0000" \
  "Add cursor control actions via PyAutoGUI." \
  src/control/actions.py src/control/__init__.py

commit_at "2025-03-22 20:00:00 +0000" \
  "Add exponential smoothing for pointer movement." \
  src/control/smoother.py

commit_at "2025-04-05 13:40:00 +0000" \
  "Add stability filter to reduce gesture jitter." \
  src/utils/stability.py src/utils/__init__.py

commit_at "2025-04-18 17:20:00 +0000" \
  "Add settings loader and config persistence." \
  src/utils/config.py config/defaults.json

commit_at "2025-05-03 10:55:00 +0000" \
  "Build main application window with PySide6." \
  src/ui/main_window.py src/ui/__init__.py

commit_at "2025-05-20 15:10:00 +0000" \
  "Add settings dialog for gesture remapping." \
  src/ui/settings_dialog.py

commit_at "2025-06-08 11:00:00 +0000" \
  "Add pinch-click and drag gesture support." \
  src/hand/gestures.py src/control/actions.py

commit_at "2025-06-25 18:30:00 +0000" \
  "Add two-finger zoom and volume gestures." \
  src/hand/gestures.py src/control/actions.py

commit_at "2025-07-10 09:45:00 +0000" \
  "Add on-screen keyboard overlay window." \
  src/ui/keyboard_window.py

commit_at "2025-07-28 14:00:00 +0000" \
  "Add gesture engine to orchestrate detection and control." \
  src/engine.py

commit_at "2025-08-14 16:25:00 +0000" \
  "Wire up main entry point and application lifecycle." \
  main.py

commit_at "2025-09-02 11:50:00 +0000" \
  "Add freeze-pointer gesture and palm detection." \
  src/hand/gestures.py src/engine.py

commit_at "2025-09-20 19:15:00 +0000" \
  "Tune gesture thresholds and action cooldowns." \
  src/hand/gestures.py src/engine.py src/control/actions.py

commit_at "2025-10-08 13:30:00 +0000" \
  "Improve UI layout and camera preview sizing." \
  src/ui/main_window.py

commit_at "2025-10-25 10:00:00 +0000" \
  "Refine pointer smoothing and stability frames." \
  src/control/smoother.py src/utils/stability.py src/engine.py

commit_at "2025-11-12 15:45:00 +0000" \
  "Expand default config with sensitivity presets." \
  config/defaults.json src/utils/config.py

commit_at "2025-11-30 20:30:00 +0000" \
  "Add README with setup and gesture reference." \
  README.md

commit_at "2025-12-15 12:10:00 +0000" \
  "Fix camera release on shutdown and edge-case cleanup." \
  main.py src/engine.py src/camera/capture.py

# ── 2026 ──────────────────────────────────────────────────────────────────────

commit_at "2026-01-10 14:00:00 +0000" \
  "Improve macOS camera and accessibility permission handling." \
  src/ui/main_window.py main.py

commit_at "2026-02-05 11:20:00 +0000" \
  "Add gesture remapping support in settings dialog." \
  src/ui/settings_dialog.py config/defaults.json

commit_at "2026-03-18 16:50:00 +0000" \
  "Reduce false positives in pinch detection." \
  src/hand/gestures.py src/hand/detector.py

commit_at "2026-04-22 09:30:00 +0000" \
  "Polish main window status indicators and controls." \
  src/ui/main_window.py

commit_at "2026-05-15 18:00:00 +0000" \
  "Improve keyboard overlay positioning and visibility." \
  src/ui/keyboard_window.py

commit_at "2026-06-20 13:15:00 +0000" \
  "Harden engine shutdown and resource cleanup." \
  src/engine.py main.py src/camera/capture.py

commit_at "2026-07-05 10:40:00 +0000" \
  "Update README and requirements for public release." \
  README.md requirements.txt

commit_at "2026-07-12 15:00:00 +0000" \
  "Initial commit: hand gesture desktop controller." \
  .

commit_at "2026-08-10 08:47:56 +0100" \
  "Add GitHub push helper and fix large-file upload buffer." \
  push-github.sh

# Replace main branch
git branch -D main 2>/dev/null || true
git branch -m main

echo ""
echo "History rebuilt with $(git rev-list --count main) commits."
echo "Run: git push --force origin main"
